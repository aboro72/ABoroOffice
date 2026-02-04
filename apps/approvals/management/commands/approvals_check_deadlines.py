from django.core.management.base import BaseCommand

from apps.approvals.celery_tasks import check_approval_deadlines


class Command(BaseCommand):
    help = 'Check approval deadlines and mark expired approvals'

    def handle(self, *args, **options):
        result = check_approval_deadlines()
        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Checked deadlines: expired {result.get('expired_count', 0)}"
                )
            )
        else:
            self.stderr.write(
                self.style.ERROR(f"Deadline check failed: {result.get('message')}")
            )
