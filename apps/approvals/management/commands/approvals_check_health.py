from django.core.management.base import BaseCommand

from apps.approvals.celery_tasks import check_server_health


class Command(BaseCommand):
    help = 'Check server health for rating schedules'

    def handle(self, *args, **options):
        result = check_server_health()
        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Health check complete: checked {result.get('checked_count', 0)}"
                )
            )
        else:
            self.stderr.write(
                self.style.ERROR(f"Health check failed: {result.get('message')}")
            )
