"""
Email to Ticket Handler
Automatically converts incoming emails to tickets or ticket comments
"""

import imaplib
import email
from email.header import decode_header
import re
from django.utils.timezone import now
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailToTicketHandler:
    """Handle conversion of emails to tickets"""

    def __init__(self, verbose=False, limit=None, folder=None, dry_run=False, stdout=None):
        # Get IMAP settings from database or environment
        try:
            from apps.helpdesk.helpdesk_apps.admin_panel.settings_helper import get_imap_settings
            imap_config = get_imap_settings()
            self.imap_host = imap_config['host']
            self.imap_port = imap_config['port']
            self.imap_username = imap_config['username']
            self.imap_password = imap_config['password']
            self.imap_folder = folder or imap_config['folder']
            self.imap_use_ssl = imap_config['use_ssl']
        except Exception:
            # Fallback to settings
            self.imap_host = settings.IMAP_HOST
            self.imap_port = settings.IMAP_PORT
            self.imap_username = settings.IMAP_USERNAME
            self.imap_password = settings.IMAP_PASSWORD
            self.imap_folder = folder or getattr(settings, 'IMAP_FOLDER', 'INBOX')
            self.imap_use_ssl = True

        self.verbose = verbose
        self.limit = limit
        self.dry_run = dry_run
        self.stdout = stdout
        self.server = None

    def log(self, message, style='info'):
        """Log message to console and logger"""
        if self.stdout and hasattr(self.stdout, 'style'):
            if style == 'success':
                self.stdout.write(self.stdout.style.SUCCESS(f'  ✓ {message}'))
            elif style == 'warning':
                self.stdout.write(self.stdout.style.WARNING(f'  ⚠ {message}'))
            elif style == 'error':
                self.stdout.write(self.stdout.style.ERROR(f'  ✗ {message}'))
            else:
                self.stdout.write(f'  {message}')
        elif self.stdout:
            # Fallback for stdout without style attribute
            prefix = ''
            if style == 'success':
                prefix = '✓ '
            elif style == 'warning':
                prefix = '⚠ '
            elif style == 'error':
                prefix = '✗ '
            self.stdout.write(f'{prefix}{message}')

        if style == 'error':
            logger.error(message)
        elif style == 'warning':
            logger.warning(message)
        else:
            logger.info(message)

    def connect(self):
        """Connect to IMAP server"""
        try:
            if self.imap_use_ssl or self.imap_port == 993:
                # SSL connection
                self.server = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            else:
                # Standard connection with TLS
                self.server = imaplib.IMAP4(self.imap_host, self.imap_port)
                self.server.starttls()

            self.server.login(self.imap_username, self.imap_password)
            logger.info(f"Connected to IMAP server: {self.imap_host}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from IMAP server"""
        try:
            self.server.close()
            self.server.logout()
            logger.info("Disconnected from IMAP server")
        except Exception as e:
            logger.warning(f"Error disconnecting from IMAP: {str(e)}")

    def get_email_body(self, msg):
        """Extract email body (plain text or HTML)"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body = part.get_payload(decode=True).decode('latin-1', errors='ignore')
                    break
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = msg.get_payload(decode=True).decode('latin-1', errors='ignore')

        return body.strip()

    def get_email_subject(self, msg):
        """Decode email subject"""
        subject = msg.get("Subject", "")

        if subject:
            decoded_parts = decode_header(subject)
            subject = "".join(
                part.decode(encoding or 'utf-8', errors='ignore')
                if isinstance(part, bytes) else part
                for part, encoding in decoded_parts
            )

        return subject.strip()

    def get_email_from(self, msg):
        """Extract sender email address"""
        from_header = msg.get("From", "")

        # Extract email from format: "Name <email@domain.com>" or just "email@domain.com"
        match = re.search(r'<(.+?)>', from_header)
        if match:
            return match.group(1)
        return from_header.strip()

    def extract_ticket_id(self, subject):
        """
        Extract ticket ID from subject
        Looks for patterns like: [TICKET-123], #123, Ticket #123, RE: [TICKET-123]
        """
        patterns = [
            r'\[TICKET-(\d+)\]',
            r'#(\d+)',
            r'Ticket\s+#?(\d+)',
            r'RE:\s+\[TICKET-(\d+)\]',
        ]

        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def clean_email_body(self, body):
        """Remove quoted text and signatures from email body"""
        lines = body.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip quoted lines (start with >)
            if line.strip().startswith('>'):
                continue
            # Skip signature markers
            if line.strip() in ['--', '---']:
                break
            cleaned_lines.append(line)

        # Join and remove excess whitespace
        cleaned = '\n'.join(cleaned_lines).strip()

        # Remove multiple empty lines
        while '\n\n\n' in cleaned:
            cleaned = cleaned.replace('\n\n\n', '\n\n')

        return cleaned

    def process_emails(self):
        """
        Process emails in inbox
        - First run: fetches ALL emails (full sync)
        - Subsequent runs: fetches only emails since last sync
        Returns tuple (created_count, updated_count, error_count)
        """
        from apps.helpdesk.helpdesk_apps.tickets.models import Ticket
        from django.contrib.auth import get_user_model
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
        from django.utils.timezone import now as timezone_now
        User = get_user_model()

        created_count = 0
        updated_count = 0
        error_count = 0

        if not self.connect():
            self.log("Failed to connect to IMAP server", style='error')
            return 0, 0, 1

        try:
            # Get sync settings
            try:
                settings_obj = SystemSettings.get_settings()
            except:
                settings_obj = None

            # Select inbox
            self.server.select(self.imap_folder)

            # Determine search criteria
            if settings_obj and settings_obj.imap_full_sync_completed and settings_obj.imap_last_sync:
                # Subsequent syncs: only get unread emails since last sync
                last_sync = settings_obj.imap_last_sync
                # Format date for IMAP: DD-Mon-YYYY (e.g., "01-Jan-2024")
                since_date = last_sync.strftime('%d-%b-%Y')
                search_criteria = f'SINCE {since_date} UNSEEN'
                if self.verbose:
                    self.log(f"Searching for unread emails since {since_date}...")
                logger.info(f"Searching for unread emails since {since_date}")
            else:
                # First sync: get ALL emails (unread only to avoid spam)
                search_criteria = 'UNSEEN'
                if self.verbose:
                    self.log("First sync detected - fetching all unread emails...")
                logger.info("First sync detected - fetching all unread emails")

            # Search for emails
            status, messages = self.server.search(None, search_criteria)

            if status != 'OK':
                if self.verbose:
                    self.log("No emails found matching criteria", style='warning')
                return 0, 0, 0

            email_ids = messages[0].split()

            if not email_ids:
                if self.verbose:
                    self.log("No emails to process")
                return 0, 0, 0

            # Apply limit if specified
            if self.limit:
                email_ids = email_ids[:self.limit]

            if self.verbose:
                self.log(f"Processing {len(email_ids)} email(s)...")
            else:
                logger.info(f"Processing {len(email_ids)} emails...")

            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = self.server.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        error_count += 1
                        continue

                    msg = email.message_from_bytes(msg_data[0][1])

                    # Extract email components
                    subject = self.get_email_subject(msg)
                    sender_email = self.get_email_from(msg)
                    body = self.get_email_body(msg)
                    body = self.clean_email_body(body)

                    if self.verbose:
                        self.log(f"From: {sender_email} | Subject: {subject[:50]}...")
                    else:
                        logger.info(f"Processing email from {sender_email}: {subject}")

                    # Try to extract ticket ID
                    ticket_id = self.extract_ticket_id(subject)

                    if ticket_id:
                        # Add as comment to existing ticket
                        try:
                            ticket = Ticket.objects.get(id=ticket_id)

                            if not self.dry_run:
                                # Create comment
                                from apps.helpdesk.helpdesk_apps.tickets.models import TicketComment
                                comment = TicketComment(
                                    ticket=ticket,
                                    author_name=sender_email,
                                    author_email=sender_email,
                                    content=body,
                                    message=body,
                                    is_internal=False,
                                    is_from_email=True
                                )
                                comment.save()

                                # Mark email as read
                                self.server.store(email_id, '+FLAGS', '\\Seen')

                                self.log(f"Added comment to Ticket #{ticket_id}", style='success')
                            else:
                                self.log(f"[DRY-RUN] Would add comment to Ticket #{ticket_id}", style='warning')

                            updated_count += 1

                        except Ticket.DoesNotExist:
                            if self.verbose:
                                self.log(f"Ticket #{ticket_id} not found, creating new ticket")
                            else:
                                logger.warning(f"Ticket #{ticket_id} not found, creating new ticket")
                            # Fall through to create new ticket
                            ticket_id = None

                    if not ticket_id:
                        # Create new ticket
                        try:
                            if not self.dry_run:
                                # Get or create user from email
                                user, created = User.objects.get_or_create(
                                    email=sender_email,
                                    defaults={
                                        'username': sender_email.split('@')[0],
                                        'full_name': sender_email,
                                        'role': 'customer',
                                    }
                                )

                                # Create ticket
                                ticket = Ticket.objects.create(
                                    title=subject or "Email without subject",
                                    description=body,
                                    customer=user,
                                    priority='medium',
                                    status='open',
                                    created_from_email=True,
                                    email_from=sender_email,
                                )

                                # Mark email as read
                                self.server.store(email_id, '+FLAGS', '\\Seen')

                                self.log(f"Created new Ticket #{ticket.ticket_number}", style='success')
                            else:
                                self.log(f"[DRY-RUN] Would create Ticket: {subject[:40]}...", style='warning')

                            logger.info(f"Created new Ticket from email from {sender_email}")
                            created_count += 1

                        except Exception as e:
                            logger.error(f"Failed to create ticket: {str(e)}")
                            error_count += 1

                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {str(e)}")
                    error_count += 1

        finally:
            self.disconnect()

        # Update sync tracking if no errors and at least one email was processed
        if not self.dry_run and (created_count > 0 or updated_count > 0):
            try:
                from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
                from django.utils.timezone import now as timezone_now

                settings_obj = SystemSettings.get_settings()
                settings_obj.imap_last_sync = timezone_now()

                # Mark full sync as completed after first run
                if not settings_obj.imap_full_sync_completed:
                    settings_obj.imap_full_sync_completed = True
                    if self.verbose:
                        self.log("Full sync completed - subsequent syncs will be incremental", style='success')
                    logger.info("Full sync completed - subsequent syncs will be incremental")

                settings_obj.save(update_fields=['imap_last_sync', 'imap_full_sync_completed'])
                logger.info(f"Updated last sync timestamp: {settings_obj.imap_last_sync}")
            except Exception as e:
                logger.warning(f"Failed to update sync timestamp: {str(e)}")

        logger.info(f"Email processing completed: Created={created_count}, Updated={updated_count}, Errors={error_count}")
        return created_count, updated_count, error_count


def process_incoming_emails():
    """Celery task wrapper for email processing"""
    handler = EmailToTicketHandler()
    created, updated, errors = handler.process_emails()
    return {
        'created': created,
        'updated': updated,
        'errors': errors,
    }
