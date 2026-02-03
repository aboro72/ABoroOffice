"""
Business logic services for classroom app.
Handles email reminders, notifications, and deployment operations.
"""

import logging
from django.core.mail import send_mail
from django.utils import timezone
from .models import EmailReminder

logger = logging.getLogger(__name__)


class EmailReminderService:
    """
    Service for managing email reminders for classroom deployments.
    Sends reminder emails for shipping and pickup dates.
    """

    @staticmethod
    def send_pending_reminders():
        """
        Send all pending email reminders.
        Should be called by Celery task periodically.
        """
        now = timezone.now()
        pending_reminders = EmailReminder.objects.filter(
            sent=False,
            send_date__lte=now
        )

        count = 0
        for reminder in pending_reminders:
            if EmailReminderService.send_reminder(reminder):
                count += 1

        logger.info(f"Sent {count} email reminders")
        return count

    @staticmethod
    def send_reminder(reminder):
        """
        Send a single email reminder.

        Args:
            reminder: EmailReminder instance

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            deployment = reminder.deployment
            if not deployment:
                logger.warning(f"Reminder {reminder.id} has no associated deployment")
                return False

            subject = f"Classroom {deployment.classroom.name} - {reminder.get_reminder_type_display()} Reminder"

            if reminder.reminder_type == 'versand':
                message = f"""
Dear Team,

This is a reminder that classroom {deployment.classroom.name} is scheduled to be shipped to {deployment.location.name} on {deployment.shipping_date}.

Deployment dates: {deployment.deployment_start} to {deployment.deployment_end}

Please ensure all preparations are complete.

Best regards,
ABoroOffice System
"""
            else:  # abholung
                message = f"""
Dear Team,

This is a reminder that classroom {deployment.classroom.name} will be returned from {deployment.location.name} on {deployment.pickup_date}.

Please ensure the location is prepared for pickup.

Best regards,
ABoroOffice System
"""

            # TODO: Get recipient email from settings/admin configuration
            recipient_list = ['admin@example.com']

            send_mail(
                subject,
                message,
                'noreply@aboro.office',
                recipient_list,
                fail_silently=False,
            )

            reminder.sent = True
            reminder.sent_at = timezone.now()
            reminder.save()

            logger.info(f"Reminder {reminder.id} sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send reminder {reminder.id}: {str(e)}")
            return False


class DeploymentService:
    """
    Service for classroom deployment operations.
    Handles availability checks and scheduling.
    """

    @staticmethod
    def check_availability(classroom, start_date, end_date, **kwargs):
        """
        Check if a classroom is available for the given period.

        Args:
            classroom: MobileClassroom instance
            start_date: Start date
            end_date: End date
            **kwargs: Additional parameters (shipping_date, pickup_date, etc.)

        Returns:
            tuple: (is_available, reason)
        """
        return classroom.is_available_for_deployment(
            start_date, end_date, **kwargs
        )

    @staticmethod
    def get_available_classrooms(start_date, end_date, **kwargs):
        """
        Get all available classrooms for the given period.

        Args:
            start_date: Start date
            end_date: End date
            **kwargs: Additional parameters

        Returns:
            QuerySet: Available classrooms
        """
        from .models import MobileClassroom
        return MobileClassroom.get_available_classrooms(
            start_date, end_date, **kwargs
        )

    @staticmethod
    def suggest_classroom(start_date, end_date, **kwargs):
        """
        Get a suggested classroom for the given period.

        Args:
            start_date: Start date
            end_date: End date
            **kwargs: Additional parameters

        Returns:
            MobileClassroom: Suggested classroom or None
        """
        from .models import MobileClassroom
        return MobileClassroom.get_suggested_classroom(
            start_date, end_date, **kwargs
        )
