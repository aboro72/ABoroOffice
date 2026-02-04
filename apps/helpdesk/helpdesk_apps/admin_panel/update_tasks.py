"""
Celery tasks for automatic update checking
"""

from celery import shared_task
from django.conf import settings
from .update_manager import check_and_notify_updates, install_updates_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_for_updates_task(self):
    """
    Periodic task to check for system updates
    Runs every 6 hours by default
    """
    try:
        result = check_and_notify_updates()
        logger.info(f"Update check completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Error checking for updates: {str(exc)}")
        # Retry with exponential backoff
        retry_in = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=retry_in * 60)


@shared_task(bind=True, max_retries=3)
def install_pending_updates_task(self, notification_id):
    """
    Task to automatically install pending updates
    Can be called manually or scheduled
    """
    try:
        result = install_updates_task(notification_id)
        logger.info(f"Update installation completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Error installing updates: {str(exc)}")
        # Retry with exponential backoff
        retry_in = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=retry_in * 60)


# Optional: Auto-install updates if enabled
@shared_task
def auto_install_updates():
    """
    Automatically install available updates if AUTO_UPDATE is enabled
    """
    auto_update = getattr(settings, 'AUTO_UPDATE', False)

    if not auto_update:
        logger.info("Auto-update is disabled")
        return {'status': 'disabled'}

    try:
        from .update_manager import UpdateNotification

        # Get latest uninstalled update
        pending = UpdateNotification.objects.filter(
            installed=False
        ).latest('created_at')

        if not pending:
            return {'status': 'no_pending_updates'}

        result = install_updates_task(pending.id)
        return result

    except UpdateNotification.DoesNotExist:
        return {'status': 'no_pending_updates'}
    except Exception as e:
        logger.error(f"Error in auto-install: {str(e)}")
        return {'status': 'error', 'error': str(e)}
