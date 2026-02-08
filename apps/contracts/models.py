from django.db import models
from django.conf import settings


class Contract(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('active', 'Aktiv'),
        ('expired', 'Abgelaufen'),
        ('terminated', 'Beendet'),
    ]

    title = models.CharField(max_length=255)
    counterparty = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    value_eur = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
    )
    file = models.FileField(upload_to='contracts/', blank=True)
    notes = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    ai_risks = models.JSONField(default=list, blank=True)
    ai_checklist = models.JSONField(default=list, blank=True)
    ai_key_dates = models.JSONField(default=list, blank=True)
    ai_last_analyzed = models.DateTimeField(null=True, blank=True)
    ai_status = models.CharField(max_length=20, default='idle')
    ai_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ContractVersion(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='versions')
    label = models.CharField(max_length=100, default='v1')
    file = models.FileField(upload_to='contracts/versions/', blank=True)
    summary = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contract.title} - {self.label}"
