"""
Django signals for classroom app.
Handles automatic creation of email reminders and deployment history.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from .models import (
    ClassroomDeployment, DeploymentHistory, EmailReminder
)


@receiver(post_save, sender=ClassroomDeployment)
def create_email_reminders_on_deployment_creation(sender, instance, created, **kwargs):
    """
    Create email reminders when a ClassroomDeployment is created.
    Sends reminders 7 days before shipping and 7 days before pickup.
    """
    if not created:
        return

    # Create shipping reminder (7 days before shipping date)
    if instance.shipping_date:
        shipping_reminder_date = instance.shipping_date - timedelta(days=7)
        EmailReminder.objects.get_or_create(
            deployment=instance,
            reminder_type='versand',
            send_date=shipping_reminder_date,
            defaults={
                'classroom': instance.classroom,
            }
        )

    # Create pickup reminder (7 days before pickup date)
    if instance.pickup_date:
        pickup_reminder_date = instance.pickup_date - timedelta(days=7)
        EmailReminder.objects.get_or_create(
            deployment=instance,
            reminder_type='abholung',
            send_date=pickup_reminder_date,
            defaults={
                'classroom': instance.classroom,
            }
        )


@receiver(post_save, sender=ClassroomDeployment)
def create_initial_deployment_history(sender, instance, created, **kwargs):
    """
    Create initial deployment history entry when deployment is created.
    """
    if not created:
        return

    # Create initial history entry
    DeploymentHistory.objects.create(
        deployment=instance,
        event_type='versand_geplant',
        event_date=instance.created_at,
        notes=f'Deployment planned: {instance.classroom.name} -> {instance.location.name}'
    )
