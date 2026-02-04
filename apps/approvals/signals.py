"""
Django signals for Approvals App
Handles automatic actions on model changes
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Approval

logger = logging.getLogger('approvals')


@receiver(post_save, sender=Approval)
def on_approval_created(sender, instance, created, **kwargs):
    """
    Signal handler when Approval is created
    Sends initial email and schedules reminders
    """
    if created:
        logger.info(f"New approval created: {instance.token}")

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
        # Check if status changed from pending to approved
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return

        if old_instance.status != 'approved' and instance.status == 'approved':
            logger.info(f"Approval approved: {instance.token}")

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
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return

        if old_instance.status != 'rejected' and instance.status == 'rejected':
            logger.info(f"Approval rejected: {instance.token}")

            # Import here to avoid circular imports
            from .celery_tasks import send_approval_rejected_email_task

            # Send rejection email
            send_approval_rejected_email_task.delay(instance.id)
            logger.info(f"Queued rejection email for {instance.token}")
