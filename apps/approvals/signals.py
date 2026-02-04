"""
Django signals for Approvals App
Handles automatic actions on model changes
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Approval

logger = logging.getLogger('approvals')


@receiver(pre_save, sender=Approval)
def cache_previous_status(sender, instance, **kwargs):
    """
    Cache previous status so post_save handlers can detect transitions.
    """
    if instance.pk:
        try:
            previous = sender.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
            instance._previous_execution_status = previous.execution_status
        except sender.DoesNotExist:
            instance._previous_status = None
            instance._previous_execution_status = None
    else:
        instance._previous_status = None
        instance._previous_execution_status = None


def _log_with_context(instance, fallback_action, details=None):
    """Write an audit log using any provided context or fallback values."""
    context = getattr(instance, '_audit_context', None)
    if context:
        instance.log_action(**context)
        delattr(instance, '_audit_context')
        return True

    instance.log_action(
        action=fallback_action,
        actor_label='system',
        method='auto',
        details=details or {},
    )
    return True


@receiver(post_save, sender=Approval)
def on_approval_created(sender, instance, created, **kwargs):
    """
    Signal handler when Approval is created
    Sends initial email and schedules reminders
    """
    if created:
        logger.info(f"New approval created: {instance.token}")
        _log_with_context(instance, 'created')

        # Import here to avoid circular imports
        from .celery_tasks import send_approval_email_task

        # Send initial approval email
        send_approval_email_task.delay(instance.id)

        logger.info(f"Queued approval email for {instance.token}")


@receiver(post_save, sender=Approval)
def on_approval_approved(sender, instance, created, **kwargs):
    """
    Signal handler when Approval is approved
    Schedules SSH execution and sends confirmation email
    """
    if not created:
        previous_status = getattr(instance, '_previous_status', None)
        if previous_status != 'approved' and instance.status == 'approved':
            logger.info(f"Approval approved: {instance.token}")
            _log_with_context(instance, 'approved')

            # Import here to avoid circular imports
            from .celery_tasks import execute_ssh_approval_task, send_approval_confirmed_email_task

            # Schedule SSH execution
            execute_ssh_approval_task.delay(instance.id)
            logger.info(f"Queued SSH execution for {instance.token}")

            # Send approval confirmation email
            send_approval_confirmed_email_task.delay(instance.id)
            logger.info(f"Queued approval confirmed email for {instance.token}")


@receiver(post_save, sender=Approval)
def on_approval_rejected(sender, instance, created, **kwargs):
    """
    Signal handler when Approval is rejected
    Sends rejection notification email
    """
    if not created:
        previous_status = getattr(instance, '_previous_status', None)
        if previous_status != 'rejected' and instance.status == 'rejected':
            logger.info(f"Approval rejected: {instance.token}")
            _log_with_context(instance, 'rejected')

            # Import here to avoid circular imports
            from .celery_tasks import send_approval_rejected_email_task

            # Send rejection email
            send_approval_rejected_email_task.delay(instance.id)
            logger.info(f"Queued rejection email for {instance.token}")


@receiver(post_save, sender=Approval)
def on_approval_expired(sender, instance, created, **kwargs):
    """
    Signal handler when Approval is expired
    """
    if not created:
        previous_status = getattr(instance, '_previous_status', None)
        if previous_status != 'expired' and instance.status == 'expired':
            logger.info(f"Approval expired: {instance.token}")
            _log_with_context(instance, 'expired')


@receiver(post_save, sender=Approval)
def on_execution_status_changed(sender, instance, created, **kwargs):
    """
    Signal handler for execution status transitions
    """
    if created:
        return

    previous_execution_status = getattr(instance, '_previous_execution_status', None)
    if previous_execution_status == instance.execution_status:
        return

    if instance.execution_status == 'in_progress':
        _log_with_context(instance, 'execution_started')
    elif instance.execution_status == 'success':
        _log_with_context(instance, 'execution_success')
    elif instance.execution_status == 'failed':
        _log_with_context(instance, 'execution_failed')
