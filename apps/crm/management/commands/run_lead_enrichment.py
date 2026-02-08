from django.core.management.base import BaseCommand
from apps.crm.models import LeadStaging
from apps.crm.services.enrichment import enrich_queryset


class Command(BaseCommand):
    help = "Run auto-enrichment for staging leads."

    def handle(self, *args, **options):
        qs = LeadStaging.objects.filter(status__in=['incomplete', 'ready'])
        count = enrich_queryset(qs)
        self.stdout.write(self.style.SUCCESS(f"Enrichment done. Updated: {count}"))
