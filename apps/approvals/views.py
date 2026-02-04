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

from .models import Approval, ApprovalSettings, RatingSchedule, ServerHealthCheck
from .celery_tasks import (
    send_approval_confirmed_email_task,
    send_approval_rejected_email_task,
)

logger = logging.getLogger('approvals')


# ============================================================================
# LIST & DETAIL VIEWS
# ============================================================================

class ApprovalListView(LoginRequiredMixin, ListView):
    """
    Display list of approvals
    Filters by status, shows pending first
    """
    model = Approval
    template_name = 'approvals/approval_list.html'
    context_object_name = 'approvals'
    paginate_by = 50

    def get_queryset(self):
        """Get approvals, filtered by status if provided"""
        queryset = Approval.objects.all().order_by('-created_at')

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


class ApprovalDetailView(LoginRequiredMixin, DetailView):
    """
    Display detailed approval information
    Shows all reminders and execution status
    """
    model = Approval
    template_name = 'approvals/approval_detail.html'
    context_object_name = 'approval'
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get_context_data(self, **kwargs):
        """Add related objects to context"""
        context = super().get_context_data(**kwargs)
        approval = self.object

        # Add reminders
        context['reminders'] = approval.approvalreminder_set.all().order_by('reminder_number')

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
            self.request.user.is_staff  # TODO: Add is_approver check
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

class ApprovalApproveView(LoginRequiredMixin, View):
    """
    Approve an approval request
    Can be triggered via:
    1. Email token link (no auth needed)
    2. Web form (auth required + staff)
    3. API endpoint
    """

    def post(self, request, token=None, pk=None):
        """Handle approval action"""
        # Get approval by token (email link) or pk (form/API)
        if token:
            approval = get_object_or_404(Approval, token=token)
        elif pk:
            approval = get_object_or_404(Approval, pk=pk)
        else:
            return JsonResponse({'error': 'No approval identifier provided'}, status=400)

        # Check permissions (if not email token)
        if not token and (not request.user.is_staff):  # TODO: Check is_approver
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
            logger.warning(f"Cannot approve {approval.token}: deadline passed")
            return JsonResponse({'error': 'Approval deadline has passed'}, status=400)

        # Approve
        try:
            approval.status = 'approved'
            approval.approved_at = timezone.now()
            approval.approved_by = request.user.email if request.user.email else request.user.username
            approval.approval_method = 'email' if token else 'gui'
            approval.save()

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


class ApprovalRejectView(LoginRequiredMixin, View):
    """
    Reject an approval request
    Requires authentication and staff permissions
    """

    @require_http_methods(["POST"])
    def post(self, request, pk):
        """Handle rejection action"""
        approval = get_object_or_404(Approval, pk=pk)

        # Check permissions
        if not request.user.is_staff:  # TODO: Check is_approver
            logger.warning(
                f"Unauthorized rejection attempt by {request.user} for {approval.token}"
            )
            return JsonResponse({'error': 'Not authorized to reject'}, status=403)

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

class ServerHealthCheckView(LoginRequiredMixin, View):
    """
    Get server health status
    Used by frontend to show server availability
    """

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


class RatingScheduleStatusView(LoginRequiredMixin, View):
    """
    Get status of rating schedules
    Shows enabled/disabled and configuration
    """

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

class ApprovalStatisticsView(LoginRequiredMixin, View):
    """
    Get approval statistics and metrics
    Shows counts by status, response times, etc.
    """

    def get(self, request):
        """Get approval statistics"""
        from django.db.models import Count, Q, Avg
        from django.utils.timezone import now, timedelta

        # Overall counts
        total = Approval.objects.count()
        pending = Approval.objects.filter(status='pending').count()
        approved = Approval.objects.filter(status='approved').count()
        rejected = Approval.objects.filter(status='rejected').count()
        expired = Approval.objects.filter(status='expired').count()

        # Calculate average approval time
        approved_with_time = Approval.objects.filter(
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
        last_week_count = Approval.objects.filter(created_at__gte=week_ago).count()

        # Most active servers
        server_stats = (
            Approval.objects
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
