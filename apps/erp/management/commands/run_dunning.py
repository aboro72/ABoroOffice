from django.core.management.base import BaseCommand
from apps.erp.services.dunning_auto import run_dunning_cycle


class Command(BaseCommand):
    help = 'Run automatic dunning cycle for overdue invoices.'

    def handle(self, *args, **options):
        result = run_dunning_cycle()
        self.stdout.write(self.style.SUCCESS(
            f"Dunning run: {result['created']} created, {result['sent']} sent"
        ))
