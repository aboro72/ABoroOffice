"""
Celery tasks for ticket management
"""

from celery import shared_task
from django.conf import settings
from .email_handler import process_incoming_emails
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_email_to_tickets(self):
    """
    Celery task to process incoming emails and convert them to tickets
    Runs every 5 minutes (configured in celery beat)
    """
    try:
        # Check if IMAP is enabled
        if not getattr(settings, 'IMAP_ENABLED', False):
            logger.warning("IMAP is not enabled, skipping email processing")
            return {
                'status': 'skipped',
                'reason': 'IMAP not enabled'
            }

        # Check if credentials are configured
        if not all([
            settings.IMAP_HOST,
            settings.IMAP_PORT,
            settings.IMAP_USERNAME,
            settings.IMAP_PASSWORD
        ]):
            logger.warning("IMAP credentials not fully configured")
            return {
                'status': 'skipped',
                'reason': 'Credentials not configured'
            }

        # Process emails
        result = process_incoming_emails()

        logger.info(f"Email processing completed: {result}")

        return {
            'status': 'success',
            'result': result
        }

    except Exception as exc:
        logger.error(f"Error processing emails: {str(exc)}", exc_info=True)

        # Retry with exponential backoff
        retry_in = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=retry_in * 60)


@shared_task
def send_ticket_reply_via_email(ticket_id, comment_id):
    """
    Task to send ticket comments/replies via email to the customer
    """
    from apps.helpdesk.helpdesk_apps.tickets.models import Ticket, TicketComment
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings

    try:
        ticket = Ticket.objects.get(id=ticket_id)
        comment = TicketComment.objects.get(id=comment_id)

        # Only send if comment is not internal
        if comment.is_internal:
            return {'status': 'skipped', 'reason': 'Internal comment'}

        # Get customer email
        customer_email = ticket.email_from or ticket.customer.email

        if not customer_email:
            logger.warning(f"No email address for Ticket #{ticket.id}")
            return {'status': 'error', 'reason': 'No email address'}

        # Prepare email context
        prefix = getattr(settings, 'HELPDESK_URL_PREFIX', '')
        context = {
            'ticket_number': ticket.ticket_number,
            'ticket_title': ticket.title,
            'comment_content': comment.content,
            'author_name': comment.author.get_full_name() if comment.author else comment.author_name,
            'site_url': settings.SITE_URL,
            'ticket_url': f"{settings.SITE_URL.rstrip('/')}{prefix}/tickets/{ticket.id}/",
        }

        # Render email template (you'll need to create this template)
        subject = f"RE: {ticket.ticket_number} - {ticket.title}"
        message = render_to_string('tickets/email_reply.html', context)

        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            html_message=message,
        )

        logger.info(f"Email sent to {customer_email} for Ticket #{ticket.id}")

        return {
            'status': 'success',
            'email': customer_email,
            'ticket_id': ticket_id
        }

    except Exception as exc:
        logger.error(f"Error sending ticket reply email: {str(exc)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(exc)
        }
