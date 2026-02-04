from django.core.management.base import BaseCommand, CommandError

from apps.approvals.celery_tasks import send_reminder_email_task
from apps.approvals.models import Approval


class Command(BaseCommand):
    help = 'Send a reminder email for a specific approval'

    def add_arguments(self, parser):
        parser.add_argument('approval_id', type=int, help='Approval ID')
        parser.add_argument('reminder_number', type=int, choices=[1, 2, 3], help='Reminder number (1-3)')

    def handle(self, *args, **options):
        approval_id = options['approval_id']
        reminder_number = options['reminder_number']

        if not Approval.objects.filter(pk=approval_id).exists():
            raise CommandError(f"Approval {approval_id} not found")

        result = send_reminder_email_task(approval_id, reminder_number)
        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Reminder {reminder_number} sent for approval {approval_id}"
                )
            )
        else:
            self.stderr.write(
                self.style.ERROR(
                    f"Reminder send failed: {result.get('message')}"
                )
            )
