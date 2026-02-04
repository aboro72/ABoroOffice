"""
Email Service for Approvals
Handles sending all approval-related emails
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('approvals')


class EmailService:
    """Service for sending approval-related emails."""

    @staticmethod
    def send_approval_request_email(approval):
        """
        Send initial approval request email.

        Args:
            approval: Approval instance

        Returns:
            dict: {'success': bool, 'message': str, 'approval_id': int}
        """
        try:
            # Build approval link
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            approval_url = f"{base_url}/approvals/{approval.token}/approve/"

            # Prepare context
            context = {
                'server_name': approval.server_name,
                'scheduled_time': approval.scheduled_time.strftime('%d.%m.%Y %H:%M:%S'),
                'deadline': approval.deadline.strftime('%d.%m.%Y %H:%M:%S'),
                'approval_url': approval_url,
                'token': str(approval.token),
            }

            # Render HTML email
            html_message = render_to_string(
                'approvals/emails/approval_request.html',
                context
            )

            # Prepare recipients
            recipients = approval.email_recipients if approval.email_recipients else []
            if not recipients:
                logger.warning(
                    f"No email recipients for approval {approval.token}. "
                    f"Check approval.email_recipients or RatingSchedule.approval_email_recipients"
                )
                return {
                    'success': False,
                    'message': 'No email recipients configured',
                    'approval_id': approval.id,
                }

            # Send email
            email = EmailMultiAlternatives(
                subject=f'[ABoroOffice] Genehmigung erforderlich: {approval.server_name}',
                body=f'Genehmigung erforderlich für {approval.server_name}. Besuchen Sie {approval_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.attach_alternative(html_message, 'text/html')
            email.send(fail_silently=False)

            # Mark email as sent
            approval.initial_email_sent = True
            approval.save(update_fields=['initial_email_sent'])
            approval.log_action(
                action='email_sent',
                actor_label='system',
                method='email',
                details={'type': 'approval_request', 'recipients': recipients},
            )

            logger.info(
                f"Approval request email sent for {approval.token} to {recipients}"
            )

            return {
                'success': True,
                'message': 'Approval request email sent',
                'approval_id': approval.id,
                'recipients': recipients,
            }

        except Exception as e:
            logger.error(f"Failed to send approval request email: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Email send failed: {str(e)}',
                'approval_id': approval.id,
            }

    @staticmethod
    def send_reminder_email(approval, reminder_number):
        """
        Send reminder email (1, 2, or 3).

        Args:
            approval: Approval instance
            reminder_number: 1, 2, or 3

        Returns:
            dict: {'success': bool, 'message': str}
        """
        if reminder_number not in [1, 2, 3]:
            return {'success': False, 'message': 'Invalid reminder number'}

        try:
            # Check if reminder was already sent
            if reminder_number == 1 and approval.reminder_1_sent:
                logger.info(f"Reminder 1 already sent for {approval.token}")
                return {'success': False, 'message': 'Reminder 1 already sent'}
            elif reminder_number == 2 and approval.reminder_2_sent:
                logger.info(f"Reminder 2 already sent for {approval.token}")
                return {'success': False, 'message': 'Reminder 2 already sent'}
            elif reminder_number == 3 and approval.reminder_3_sent:
                logger.info(f"Reminder 3 already sent for {approval.token}")
                return {'success': False, 'message': 'Reminder 3 already sent'}

            # Calculate time remaining
            now = timezone.now()
            time_diff = approval.deadline - now
            hours_remaining = max(0, int(time_diff.total_seconds() / 3600))

            # Build approval link
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            approval_url = f"{base_url}/approvals/{approval.token}/approve/"

            # Select template and context based on reminder number
            if reminder_number == 1:
                template = 'approvals/emails/reminder_1.html'
                subject = f'[ABoroOffice] Erinnerung: Genehmigung erforderlich für {approval.server_name}'
                reminder_time = '14:00'
            elif reminder_number == 2:
                template = 'approvals/emails/reminder_2.html'
                subject = f'[ABoroOffice] FINAL ERINNERUNG: {approval.server_name}'
                reminder_time = '20:00'
            else:  # reminder_number == 3
                template = 'approvals/emails/reminder_3.html'
                subject = f'[ABoroOffice] LETZTER AUFRUF: {approval.server_name}'
                reminder_time = '07:00'

            context = {
                'server_name': approval.server_name,
                'scheduled_time': approval.scheduled_time.strftime('%d.%m.%Y %H:%M:%S'),
                'deadline': approval.deadline.strftime('%d.%m.%Y %H:%M:%S'),
                'approval_url': approval_url,
                'hours_remaining': hours_remaining,
                'token': str(approval.token),
            }

            # Render HTML email
            html_message = render_to_string(template, context)

            # Prepare recipients
            recipients = approval.email_recipients if approval.email_recipients else []
            if not recipients:
                logger.warning(f"No email recipients for reminder {reminder_number}")
                return {'success': False, 'message': 'No recipients'}

            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=f'Reminder {reminder_number}: Genehmigung erforderlich. {approval_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.attach_alternative(html_message, 'text/html')
            email.send(fail_silently=False)

            # Mark reminder as sent
            if reminder_number == 1:
                approval.reminder_1_sent = True
                approval.reminder_1_time = reminder_time
            elif reminder_number == 2:
                approval.reminder_2_sent = True
                approval.reminder_2_time = reminder_time
            else:
                approval.reminder_3_sent = True
                approval.reminder_3_time = reminder_time

            approval.save()
            approval.log_action(
                action='email_sent',
                actor_label='system',
                method='email',
                details={'type': f'reminder_{reminder_number}', 'recipients': recipients},
            )

            logger.info(f"Reminder {reminder_number} email sent for {approval.token}")

            return {
                'success': True,
                'message': f'Reminder {reminder_number} email sent',
                'approval_id': approval.id,
                'recipients': recipients,
            }

        except Exception as e:
            logger.error(
                f"Failed to send reminder {reminder_number} email: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'message': f'Email send failed: {str(e)}',
            }

    @staticmethod
    def send_approval_confirmed_email(approval):
        """
        Send email when approval is confirmed (approved).

        Args:
            approval: Approval instance

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Prepare context
            context = {
                'server_name': approval.server_name,
                'approved_by': approval.approved_by,
                'approved_at': approval.approved_at.strftime('%d.%m.%Y %H:%M:%S') if approval.approved_at else '-',
                'approval_method': approval.get_approval_method_display(),
                'scheduled_time': approval.scheduled_time.strftime('%d.%m.%Y %H:%M:%S'),
            }

            # Render HTML email
            html_message = render_to_string(
                'approvals/emails/approval_approved.html',
                context
            )

            # Prepare recipients (notify approvers)
            recipients = approval.email_recipients if approval.email_recipients else []
            if not recipients:
                logger.warning(f"No recipients to notify for approval {approval.token}")
                return {'success': False, 'message': 'No recipients'}

            # Send email
            email = EmailMultiAlternatives(
                subject=f'[ABoroOffice] Genehmigung bestätigt: {approval.server_name}',
                body=f'Genehmigung für {approval.server_name} wurde akzeptiert.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.attach_alternative(html_message, 'text/html')
            email.send(fail_silently=False)

            logger.info(f"Approval confirmed email sent for {approval.token}")
            approval.log_action(
                action='email_sent',
                actor_label='system',
                method='email',
                details={'type': 'approved_confirmation', 'recipients': recipients},
            )

            return {
                'success': True,
                'message': 'Confirmation email sent',
                'approval_id': approval.id,
            }

        except Exception as e:
            logger.error(f"Failed to send approval confirmed email: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Email send failed: {str(e)}',
            }

    @staticmethod
    def send_approval_rejected_email(approval):
        """
        Send email when approval is rejected.

        Args:
            approval: Approval instance

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Prepare context
            context = {
                'server_name': approval.server_name,
                'rejected_by': approval.approved_by or 'Unknown',
                'rejected_at': timezone.now().strftime('%d.%m.%Y %H:%M:%S'),
                'reason': approval.notes or 'No reason provided',
            }

            # Render HTML email
            html_message = render_to_string(
                'approvals/emails/approval_rejected.html',
                context
            )

            # Prepare recipients
            recipients = approval.email_recipients if approval.email_recipients else []
            if not recipients:
                logger.warning(f"No recipients to notify for rejection {approval.token}")
                return {'success': False, 'message': 'No recipients'}

            # Send email
            email = EmailMultiAlternatives(
                subject=f'[ABoroOffice] Genehmigung abgelehnt: {approval.server_name}',
                body=f'Genehmigung für {approval.server_name} wurde abgelehnt.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients,
            )
            email.attach_alternative(html_message, 'text/html')
            email.send(fail_silently=False)

            logger.info(f"Approval rejection email sent for {approval.token}")
            approval.log_action(
                action='email_sent',
                actor_label='system',
                method='email',
                details={'type': 'rejected_notification', 'recipients': recipients},
            )

            return {
                'success': True,
                'message': 'Rejection email sent',
                'approval_id': approval.id,
            }

        except Exception as e:
            logger.error(f"Failed to send approval rejected email: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Email send failed: {str(e)}',
            }
