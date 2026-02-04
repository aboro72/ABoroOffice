"""
Views for the Approvals app
Handles HTTP requests for approval workflows
"""

import logging
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from .models import Approval, ApprovalSettings, RatingSchedule, ServerHealthCheck
from .celery_tasks import (
    send_approval_confirmed_email_task,
    send_approval_rejected_email_task,
)
from apps.licensing.decorators import license_required, LicenseRequiredMixin, ApproverRequiredMixin

logger = logging.getLogger('approvals')


def _get_client_ip(request):
    """Best-effort client IP extraction."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _check_rate_limit(key, max_count, period_seconds):
    """Simple cache-based rate limiter."""
    current = cache.get(key, 0)
    if current >= max_count:
        return False
    if current == 0:
        cache.set(key, 1, timeout=period_seconds)
    else:
        cache.incr(key)
    return True


# ============================================================================
# LIST & DETAIL VIEWS
# ============================================================================

class ApprovalListView(LicenseRequiredMixin, LoginRequiredMixin, ListView):
    """
    Display list of approvals
    Filters by status, shows pending first
    """
    model = Approval
    template_name = 'approvals/approval_list.html'
    context_object_name = 'approvals'
    paginate_by = 50
    required_feature = 'approvals'

    def get_queryset(self):
        """Get approvals, filtered by status if provided"""
        queryset = (
            Approval.objects
            .select_related('rating_schedule')
            .prefetch_related('reminders')
            .filter(archived=False)
            .order_by('-created_at')
        )

        # Filter by status
        status = self.request.GET.get('status')
        if status in ['pending', 'approved', 'rejected', 'expired']:
            queryset = queryset.filter(status=status)

        # Filter by server
        server = self.request.GET.get('server')
        if server:
            queryset = queryset.filter(server_name__icontains=server)

        return queryset

    def get_context_data(self, **kwargs):
        """Add filter info to context"""
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ['pending', 'approved', 'rejected', 'expired']
        context['current_status'] = self.request.GET.get('status', '')
        context['current_server'] = self.request.GET.get('server', '')
        return context


class ApprovalDetailView(LicenseRequiredMixin, LoginRequiredMixin, DetailView):
    """
    Display detailed approval information
    Shows all reminders and execution status
    """
    model = Approval
    template_name = 'approvals/approval_detail.html'
    context_object_name = 'approval'
    slug_field = 'token'
    slug_url_kwarg = 'token'
    required_feature = 'approvals'

    def get_queryset(self):
        return (
            Approval.objects
            .select_related('rating_schedule')
            .prefetch_related('reminders', 'audit_logs')
            .filter(archived=False)
        )

    def get_context_data(self, **kwargs):
        """Add related objects to context"""
        context = super().get_context_data(**kwargs)
        approval = self.object

        # Add reminders
        context['reminders'] = approval.reminders.all().order_by('reminder_number')

        # Add health status
        try:
            context['server_health'] = ServerHealthCheck.objects.get(
                server_name=approval.server_name
            )
        except ServerHealthCheck.DoesNotExist:
            context['server_health'] = None

        # Check if user can approve
        context['can_approve'] = (
            approval.status == 'pending' and
            not approval.is_expired() and
            approval.user_can_approve(self.request.user)
        )

        # Hours remaining
        if approval.status == 'pending' and not approval.is_expired():
            time_left = approval.deadline - timezone.now()
            hours_left = time_left.total_seconds() / 3600
            context['hours_remaining'] = max(0, round(hours_left, 1))

        return context


# ============================================================================
# APPROVAL WORKFLOW VIEWS
# ============================================================================

class ApprovalApproveView(View):
    """
    Approve an approval request
    Can be triggered via:
    1. Email token link (no auth needed)
    2. Web form (auth required + staff/approver)
    3. API endpoint
    """

    def post(self, request, token=None, pk=None):
        """Handle approval action"""
        client_ip = _get_client_ip(request)

        # Rate limit token-based approvals (email links)
        if token:
            rate_limit = getattr(
                settings,
                'APPROVALS_RATE_LIMIT',
                {'count': 10, 'period': 600},
            )
            if not _check_rate_limit(
                key=f"approvals:approve:{token}:{client_ip}",
                max_count=rate_limit.get('count', 10),
                period_seconds=rate_limit.get('period', 600),
            ):
                logger.warning(f"Rate limit exceeded for approval token {token} from {client_ip}")
                return JsonResponse({'error': 'Rate limit exceeded'}, status=429)

        # Get approval by token (email link) or pk (form/API)
        if token:
            approval = get_object_or_404(Approval, token=token)
        elif pk:
            approval = get_object_or_404(Approval, pk=pk)
        else:
            return JsonResponse({'error': 'No approval identifier provided'}, status=400)

        # Check permissions (if not email token)
        if not token:
            # Require authentication
            if not request.user.is_authenticated:
                logger.warning(f"Unauthenticated approval attempt for {approval.token}")
                return JsonResponse({'error': 'Authentication required'}, status=401)

            # Check license (if enabled)
            if getattr(settings, 'LICENSE_CHECK_ENABLED', True) and not request.user.can_access_feature('approvals'):
                logger.warning(f"License check failed for {request.user}")
                return JsonResponse({'error': 'Feature not available in license'}, status=403)

            # Check approver status and group access
            if not approval.user_can_approve(request.user):
                logger.warning(
                    f"Unauthorized approval attempt by {request.user} for {approval.token}"
                )
                return JsonResponse({'error': 'Not authorized to approve'}, status=403)

        # Check if already approved/rejected
        if approval.status in ['approved', 'rejected', 'expired']:
            logger.warning(f"Cannot approve {approval.token}: status is {approval.status}")
            return JsonResponse({
                'error': f'Approval already {approval.status}'
            }, status=400)

        # Check if expired
        if approval.is_expired():
            approval._audit_context = {
                'action': 'expired',
                'actor_user': request.user if request.user.is_authenticated else None,
                'actor_label': 'system',
                'method': 'auto',
                'ip_address': client_ip,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'details': {'reason': 'deadline_passed'},
            }
            approval.mark_expired()
            logger.warning(f"Cannot approve {approval.token}: deadline passed")
            return JsonResponse({'error': 'Approval deadline has passed'}, status=400)

        # Approve
        try:
            approval.status = 'approved'
            approval.approved_at = timezone.now()
            if token:
                approval.approved_by = 'email-token'
                approval.approval_method = 'email'
            else:
                approval.approved_by = request.user.email if request.user.email else request.user.username
                approval.approval_method = 'gui'
            approval._audit_context = {
                'action': 'approved',
                'actor_user': request.user if request.user.is_authenticated else None,
                'actor_label': approval.approved_by or 'email-token',
                'method': approval.approval_method,
                'ip_address': client_ip,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
            approval.save()
            approval.log_action(
                action='approved',
                actor_user=request.user if request.user.is_authenticated else None,
                actor_label=approval.approved_by or 'email-token',
                method=approval.approval_method,
                ip_address=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )

            logger.info(
                f"Approval approved: {approval.token} by {approval.approved_by} "
                f"via {approval.approval_method}"
            )

            # Return response based on request type
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Approval granted',
                    'status': approval.status,
                    'approved_by': approval.approved_by,
                    'approved_at': approval.approved_at.isoformat()
                })
            else:
                # Redirect to success page
                return redirect('approval-detail', token=approval.token)

        except Exception as exc:
            logger.error(f"Error approving {approval.token}: {str(exc)}", exc_info=True)
            return JsonResponse({
                'error': f'Error: {str(exc)}'
            }, status=500)


class ApprovalRejectView(ApproverRequiredMixin, LoginRequiredMixin, View):
    """
    Reject an approval request
    Requires authentication and approver permissions
    """

    @require_http_methods(["POST"])
    def post(self, request, pk):
        """Handle rejection action"""
        approval = get_object_or_404(Approval, pk=pk)
        client_ip = _get_client_ip(request)

        # ApproverRequiredMixin already checks basic permissions in dispatch
        # Additional license and group checks
        if getattr(settings, 'LICENSE_CHECK_ENABLED', True) and not request.user.can_access_feature('approvals'):
            logger.warning(f"License check failed for {request.user}")
            return JsonResponse({'error': 'Feature not available in license'}, status=403)
        if not approval.user_can_approve(request.user):
            logger.warning(f"Approval group check failed for {request.user} on {approval.token}")
            return JsonResponse({'error': 'Not authorized to approve'}, status=403)

        # Check if already approved/rejected
        if approval.status in ['approved', 'rejected', 'expired']:
            logger.warning(f"Cannot reject {approval.token}: status is {approval.status}")
            return JsonResponse({
                'error': f'Approval already {approval.status}'
            }, status=400)

        # Get rejection reason
        reason = request.POST.get('reason', '') or request.GET.get('reason', '')

        # Reject
        try:
            approval.status = 'rejected'
            approval.approved_at = timezone.now()
            approval.approved_by = request.user.email if request.user.email else request.user.username
            approval.approval_method = 'gui'
            approval.notes = f'Rejected by {approval.approved_by}. Reason: {reason}' if reason else 'Rejected'
            approval._audit_context = {
                'action': 'rejected',
                'actor_user': request.user,
                'actor_label': approval.approved_by,
                'method': 'gui',
                'ip_address': client_ip,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'details': {'reason': reason},
            }
            approval.save()

            logger.info(
                f"Approval rejected: {approval.token} by {approval.approved_by}. "
                f"Reason: {reason}"
            )

            # Queue rejection email
            send_approval_rejected_email_task.delay(approval.id)

            # Return response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Approval rejected',
                    'status': approval.status,
                    'reason': reason
                })
            else:
                return redirect('approval-detail', token=approval.token)

        except Exception as exc:
            logger.error(f"Error rejecting {approval.token}: {str(exc)}", exc_info=True)
            return JsonResponse({
                'error': f'Error: {str(exc)}'
            }, status=500)


# ============================================================================
# HEALTH CHECK VIEWS
# ============================================================================

class ServerHealthCheckView(LicenseRequiredMixin, LoginRequiredMixin, View):
    """
    Get server health status
    Used by frontend to show server availability
    """
    required_feature = 'approvals'

    def get(self, request, server_name=None):
        """Get health status for server(s)"""
        if server_name:
            try:
                health = ServerHealthCheck.objects.get(server_name=server_name)
                return JsonResponse({
                    'success': True,
                    'server_name': health.server_name,
                    'status': health.status,
                    'is_healthy': health.is_healthy(),
                    'ssh_reachable': health.ssh_reachable,
                    'url_reachable': health.url_reachable,
                    'last_check': health.last_check.isoformat() if health.last_check else None,
                })
            except ServerHealthCheck.DoesNotExist:
                return JsonResponse({
                    'error': f'Server {server_name} not found'
                }, status=404)
        else:
            # Return all servers
            healths = ServerHealthCheck.objects.all()
            return JsonResponse({
                'success': True,
                'servers': [
                    {
                        'server_name': h.server_name,
                        'status': h.status,
                        'is_healthy': h.is_healthy(),
                        'last_check': h.last_check.isoformat() if h.last_check else None,
                    }
                    for h in healths
                ]
            })


class RatingScheduleStatusView(LicenseRequiredMixin, LoginRequiredMixin, View):
    """
    Get status of rating schedules
    Shows enabled/disabled and configuration
    """
    required_feature = 'approvals'

    def get(self, request, schedule_id=None):
        """Get schedule status"""
        if schedule_id:
            try:
                schedule = RatingSchedule.objects.get(id=schedule_id)
                return JsonResponse({
                    'success': True,
                    'id': schedule.id,
                    'display_name': schedule.display_name,
                    'enabled': schedule.enabled,
                    'abruf_zeit': str(schedule.abruf_zeit),
                    'ssh_port': schedule.ssh_port,
                    'server_url_prefix': schedule.server_url_prefix,
                })
            except RatingSchedule.DoesNotExist:
                return JsonResponse({
                    'error': f'Schedule {schedule_id} not found'
                }, status=404)
        else:
            # Return all schedules
            schedules = RatingSchedule.objects.all()
            return JsonResponse({
                'success': True,
                'schedules': [
                    {
                        'id': s.id,
                        'display_name': s.display_name,
                        'enabled': s.enabled,
                        'abruf_zeit': str(s.abruf_zeit),
                    }
                    for s in schedules
                ]
            })


# ============================================================================
# STATISTICS & REPORTING VIEWS
# ============================================================================

class ApprovalStatisticsView(LicenseRequiredMixin, LoginRequiredMixin, View):
    """
    Get approval statistics and metrics
    Shows counts by status, response times, etc.
    """
    required_feature = 'approvals'

    def get(self, request):
        """Get approval statistics"""
        from django.db.models import Count, Q, Avg
        from django.utils.timezone import now, timedelta

        # Overall counts
        base_qs = Approval.objects.filter(archived=False)
        total = base_qs.count()
        pending = base_qs.filter(status='pending').count()
        approved = base_qs.filter(status='approved').count()
        rejected = base_qs.filter(status='rejected').count()
        expired = base_qs.filter(status='expired').count()

        # Calculate average approval time
        approved_with_time = base_qs.filter(
            status='approved',
            approved_at__isnull=False,
            created_at__isnull=False
        )

        avg_approval_hours = None
        if approved_with_time.exists():
            total_time = sum(
                (a.approved_at - a.created_at).total_seconds()
                for a in approved_with_time
            )
            avg_approval_hours = round(total_time / len(approved_with_time) / 3600, 2)

        # Last 7 days stats
        week_ago = now() - timedelta(days=7)
        last_week_count = base_qs.filter(created_at__gte=week_ago).count()

        # Most active servers
        server_stats = (
            base_qs
            .values('server_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        return JsonResponse({
            'success': True,
            'statistics': {
                'total': total,
                'by_status': {
                    'pending': pending,
                    'approved': approved,
                    'rejected': rejected,
                    'expired': expired,
                },
                'avg_approval_hours': avg_approval_hours,
                'last_week': last_week_count,
                'top_servers': list(server_stats),
            }
        })
