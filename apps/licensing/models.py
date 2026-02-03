"""
Licensing models for ABoroOffice.
Defines license types and tracks active licenses.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class LicenseProduct(models.Model):
    """
    Defines available license products and their features.
    """

    TIER_CHOICES = [
        ('basic', _('Basic')),
        ('office', _('Office')),
        ('professional', _('Professional')),
        ('enterprise', _('Enterprise')),
        ('on_premise', _('On-Premise')),
        ('standalone', _('Standalone')),
    ]

    code = models.CharField(
        _('product code'),
        max_length=50,
        unique=True,
        primary_key=True,
        help_text=_('Unique product code (e.g., ABORO_BASIC, CLASSROOM_STANDALONE)')
    )
    name = models.CharField(
        _('product name'),
        max_length=255,
        help_text=_('Human-readable product name')
    )
    tier = models.CharField(
        _('tier'),
        max_length=20,
        choices=TIER_CHOICES,
        default='office'
    )
    description = models.TextField(
        _('description'),
        blank=True
    )

    # Pricing
    monthly_price = models.DecimalField(
        _('monthly price (EUR)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Leave blank for on-premise or if not applicable')
    )
    yearly_price = models.DecimalField(
        _('yearly price (EUR)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Feature limits
    max_staff_users = models.IntegerField(
        _('max staff users'),
        default=1,
        help_text=_('Maximum number of staff/agent users. -1 for unlimited')
    )
    max_total_users = models.IntegerField(
        _('max total users'),
        default=10,
        help_text=_('Maximum total users. -1 for unlimited')
    )
    storage_quota_gb = models.IntegerField(
        _('storage quota (GB)'),
        default=10,
        help_text=_('Storage quota per user. -1 for unlimited')
    )

    # Feature flags
    features = models.JSONField(
        _('features'),
        default=dict,
        help_text=_('Dictionary of feature codes and their availability')
    )

    # Status
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this product can be purchased/used')
    )

    # Metadata
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('License Product')
        verbose_name_plural = _('License Products')
        ordering = ['tier', 'code']

    def __str__(self):
        return f"{self.name} ({self.code})"


class LicenseKey(models.Model):
    """
    Represents an individual license key issued to a customer.
    """

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('expired', _('Expired')),
        ('suspended', _('Suspended')),
        ('revoked', _('Revoked')),
    ]

    # License identity
    license_code = models.CharField(
        _('license code'),
        max_length=255,
        unique=True,
        primary_key=True,
        help_text=_('Unique license code (auto-generated format)')
    )
    product = models.ForeignKey(
        LicenseProduct,
        on_delete=models.PROTECT,
        related_name='licenses',
        verbose_name=_('product')
    )

    # Customer/Owner
    customer_name = models.CharField(
        _('customer name'),
        max_length=255,
        help_text=_('Organization/individual name')
    )
    customer_email = models.EmailField(
        _('customer email'),
        help_text=_('Email for license notifications')
    )

    # Validity
    issue_date = models.DateField(
        _('issue date'),
        default=timezone.now,
        help_text=_('Date the license was issued')
    )
    expiry_date = models.DateField(
        _('expiry date'),
        help_text=_('Date the license expires')
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Deployment info
    instance_count = models.IntegerField(
        _('instance count'),
        default=1,
        help_text=_('Number of instances this license covers (for standalone/on-premise)')
    )

    # Internal notes
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Internal notes about this license')
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_licenses',
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('License Key')
        verbose_name_plural = _('License Keys')
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['customer_email']),
        ]

    def __str__(self):
        return f"{self.license_code[:20]}... ({self.product.name})"

    def is_expired(self) -> bool:
        """Check if license is expired."""
        return timezone.now().date() > self.expiry_date

    def is_valid(self) -> bool:
        """Check if license is valid and active."""
        return (
            self.status == 'active' and
            not self.is_expired()
        )

    def days_until_expiry(self) -> int:
        """Return days until expiry (negative if expired)."""
        return (self.expiry_date - timezone.now().date()).days
