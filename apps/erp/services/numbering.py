from django.db import transaction
from django.utils import timezone
from apps.erp.models import NumberSequence


def next_number(key: str, prefix: str) -> str:
    year = timezone.now().strftime('%Y')
    with transaction.atomic():
        seq, _ = NumberSequence.objects.select_for_update().get_or_create(key=key)
        seq.last_number += 1
        seq.save(update_fields=['last_number'])
        return f"{prefix}-{year}-{seq.last_number:05d}"
