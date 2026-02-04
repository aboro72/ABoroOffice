"""
Views for handling system updates in the admin panel
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .update_manager import UpdateChecker, UpdateDownloader, UpdateNotification
import logging

logger = logging.getLogger(__name__)


def is_admin(user):
    """Check if user is admin"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def check_updates_view(request):
    """Display update check results"""
    try:
        checker = UpdateChecker()
        update_info = checker.check_for_updates()

        context = {
            'has_updates': update_info.get('has_updates'),
            'file_count': update_info.get('file_count', 0),
            'updates': update_info.get('updates', {}),
            'checked_at': update_info.get('checked_at'),
            'branch': update_info.get('branch'),
            'repo': update_info.get('repo'),
            'error': update_info.get('error')
        }

        if update_info.get('has_updates'):
            # Create notification if doesn't exist
            existing = UpdateNotification.objects.filter(
                available_files__contains=list(update_info['updates'].keys())
            ).first()

            if not existing:
                notification = UpdateNotification.create_from_check(update_info)
                context['notification_id'] = notification.id if notification else None

        return render(request, 'admin_panel/updates.html', context)

    except Exception as e:
        logger.error(f"Error checking updates: {str(e)}")
        messages.error(request, f"Error checking updates: {str(e)}")
        return redirect('admin:index')


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def install_updates_view(request):
    """Install available updates"""
    try:
        notification_id = request.POST.get('notification_id')

        if not notification_id:
            # Check and install latest updates
            checker = UpdateChecker()
            update_info = checker.check_for_updates(force=True)

            if not update_info.get('has_updates'):
                return JsonResponse({
                    'status': 'already_up_to_date',
                    'message': 'System is already up to date'
                })

            # Create notification
            notification = UpdateNotification.create_from_check(update_info)
        else:
            notification = get_object_or_404(UpdateNotification, id=notification_id)

        if notification.installed:
            return JsonResponse({
                'status': 'already_installed',
                'message': 'This update has already been installed'
            })

        # Download and install
        downloader = UpdateDownloader()
        results = downloader.install_updates(notification.available_files)

        # Update notification
        notification.installed = True
        notification.save()

        logger.info(f"Updates installed: {len(results['success'])} files")

        return JsonResponse({
            'status': 'success',
            'success_count': len(results['success']),
            'failed_count': len(results['failed']),
            'results': results
        })

    except Exception as e:
        logger.error(f"Error installing updates: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_admin)
def update_history_view(request):
    """Display update history"""
    notifications = UpdateNotification.objects.all().order_by('-created_at')

    context = {
        'notifications': notifications,
        'total_updates': notifications.count(),
        'installed_updates': notifications.filter(installed=True).count()
    }

    return render(request, 'admin_panel/update_history.html', context)


@login_required
@user_passes_test(is_admin)
def force_check_updates(request):
    """Force check for updates (ignoring cache)"""
    try:
        checker = UpdateChecker()
        update_info = checker.check_for_updates(force=True)

        if update_info.get('has_updates'):
            UpdateNotification.create_from_check(update_info)
            messages.success(
                request,
                f"{update_info.get('file_count', 0)} updates available!"
            )
        else:
            messages.info(request, "System is already up to date")

        return redirect('admin_panel:check_updates')

    except Exception as e:
        logger.error(f"Error forcing update check: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('admin_panel:check_updates')


class UpdateNotificationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all update notifications"""
    model = UpdateNotification
    template_name = 'admin_panel/update_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_queryset(self):
        return UpdateNotification.objects.all().order_by('-created_at')


class UpdateNotificationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View details of a specific update"""
    model = UpdateNotification
    template_name = 'admin_panel/update_detail.html'
    context_object_name = 'notification'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
