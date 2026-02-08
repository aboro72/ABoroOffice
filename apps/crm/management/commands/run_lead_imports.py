from django.core.management.base import BaseCommand
from apps.crm.services.lead_sources import run_scheduled_imports


class Command(BaseCommand):
    help = "Run scheduled lead imports for CRM profiles."

    def handle(self, *args, **options):
        run_scheduled_imports()
        self.stdout.write(self.style.SUCCESS("Scheduled lead imports executed."))
