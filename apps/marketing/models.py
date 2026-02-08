from django.db import models
from django.conf import settings
from django.utils import timezone


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('active', 'Aktiv'),
        ('paused', 'Pausiert'),
        ('completed', 'Abgeschlossen'),
    ]

    name = models.CharField(max_length=200)
    objective = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketing_campaigns',
    )
    kpi_impressions = models.PositiveIntegerField(default=0)
    kpi_clicks = models.PositiveIntegerField(default=0)
    kpi_conversions = models.PositiveIntegerField(default=0)
    kpi_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    kpi_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_kpi_impressions = models.PositiveIntegerField(default=0)
    last_kpi_clicks = models.PositiveIntegerField(default=0)
    last_kpi_conversions = models.PositiveIntegerField(default=0)
    last_kpi_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_kpi_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_kpi_imported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def kpi_ctr(self):
        if not self.kpi_impressions:
            return 0
        return round((self.kpi_clicks / self.kpi_impressions) * 100, 2)

    def kpi_cvr(self):
        if not self.kpi_clicks:
            return 0
        return round((self.kpi_conversions / self.kpi_clicks) * 100, 2)

    def kpi_roi(self):
        if not self.kpi_spend:
            return 0
        return round(((self.kpi_revenue - self.kpi_spend) / self.kpi_spend) * 100, 2)


class CampaignKpiSnapshot(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='kpi_snapshots')
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    imported_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-imported_at']

    def __str__(self):
        return f"{self.campaign.name} - {self.imported_at:%Y-%m-%d %H:%M}"


class ContentAsset(models.Model):
    TYPE_CHOICES = [
        ('blog', 'Blog'),
        ('social', 'Social'),
        ('newsletter', 'Newsletter'),
        ('ad', 'Anzeige'),
        ('landing', 'Landingpage'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('review', 'Review'),
        ('approved', 'Freigegeben'),
        ('scheduled', 'Geplant'),
        ('published', 'Veröffentlicht'),
    ]

    title = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='social')
    channel = models.CharField(max_length=100, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    brief = models.TextField(blank=True)
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketing_assets',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ContentApproval(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('approved', 'Freigegeben'),
        ('rejected', 'Abgelehnt'),
    ]

    asset = models.ForeignKey(ContentAsset, on_delete=models.CASCADE, related_name='approvals')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketing_approvals_requested',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketing_approvals_reviewed',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.asset.title} - {self.status}"


class ContentRevision(models.Model):
    ACTION_CHOICES = [
        ('approved', 'Freigegeben'),
        ('published', 'Veröffentlicht'),
        ('rejected', 'Abgelehnt'),
    ]

    asset = models.ForeignKey(ContentAsset, on_delete=models.CASCADE, related_name='revisions')
    title = models.CharField(max_length=255)
    content = models.TextField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    note = models.TextField(blank=True)
    stamped_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketing_revisions',
    )
    stamped_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.asset.title} - {self.action}"


class ContentIdea(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_audience = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketing_ideas',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
