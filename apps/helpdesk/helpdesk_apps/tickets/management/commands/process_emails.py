"""
Django Management Command: Process Incoming Emails to Tickets
No Celery or Redis required - can be run via Cron, Task Scheduler, or manually

Usage:
    python manage.py process_emails
    python manage.py process_emails --verbose
    python manage.py process_emails --limit 10
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.helpdesk.helpdesk_apps.tickets.email_handler import EmailToTicketHandler
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process incoming emails and convert them to tickets or comments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of emails to process (default: all)',
        )

        parser.add_argument(
            '--folder',
            type=str,
            default=None,
            help='IMAP folder to process (default: INBOX)',
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually creating tickets (test mode)',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.limit = options['limit']
        self.folder = options['folder']
        self.dry_run = options['dry_run']

        if self.verbose:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] '
                    f'Starting email processing...'
                )
            )

        # Check if IMAP is enabled
        if not getattr(settings, 'IMAP_ENABLED', False):
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING('IMAP is not enabled. Set IMAP_ENABLED=True in settings.')
                )
            return

        # Check if credentials are configured
        if not all([
            settings.IMAP_HOST,
            settings.IMAP_PORT,
            settings.IMAP_USERNAME,
            settings.IMAP_PASSWORD
        ]):
            raise CommandError(
                'IMAP credentials not fully configured. Check your environment variables.'
            )

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY-RUN mode. No tickets will be created.')
            )

        try:
            handler = EmailToTicketHandler(
                verbose=self.verbose,
                limit=self.limit,
                folder=self.folder,
                dry_run=self.dry_run,
                stdout=self.stdout,
            )

            created, updated, errors = handler.process_emails()

            # Print summary
            self.print_summary(created, updated, errors)

            if errors > 0:
                self.stdout.write(
                    self.style.WARNING(f'WARNING: {errors} error(s) occurred during processing')
                )

        except Exception as e:
            raise CommandError(f'Error during email processing: {str(e)}')

    def print_summary(self, created, updated, errors):
        """Print processing summary"""
        summary_msg = (
            f'Email Processing Summary:\n'
            f'  Created: {created} new ticket(s)\n'
            f'  Updated: {updated} ticket(s)\n'
            f'  Errors: {errors}'
        )

        if created > 0 or updated > 0:
            self.stdout.write(self.style.SUCCESS(summary_msg))
        else:
            self.stdout.write(self.style.WARNING(summary_msg))
