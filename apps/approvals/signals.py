"""
Django signals for Approvals App
Handles automatic actions on model changes
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Approval


@receiver(post_save, sender=Approval)
def on_approval_created(sender, instance, created, **kwargs):
    """
    Signal handler when Approval is created
    Future: Send initial email, schedule reminders
    """
    if created:
        # TODO: Send initial approval email
        # TODO: Schedule reminder tasks
        pass


@receiver(post_save, sender=Approval)
def on_approval_approved(sender, instance, created, **kwargs):
    """
    Signal handler when Approval is approved
    Future: Schedule SSH execution
    """
    if not created and instance.status == 'approved':
        # TODO: Schedule SSH execution task
        # TODO: Send approval confirmation email
        pass
