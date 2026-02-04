"""
Core models for ABoroOffice.
Unified user model and shared settings.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ABoroUser(AbstractUser):
    """
    Unified user model consolidating fields from all integrated applications:
    - HelpDesk: department, is_agent, support_level
    - Cloude: two_factor_enabled, storage_quota_mb
    - Pit-Kalendar: -
    - dokmbw_web_app: -
    - Shared: phone, timezone
    """

    ROLE_CHOICES = [
        ('admin', _('Administrator')),
        ('support_agent', _('Support Agent')),
        ('customer', _('Customer')),
        ('classroom_manager', _('Classroom Manager')),
        ('approvals_officer', _('Approvals Officer')),
    ]

    SUPPORT_LEVEL_CHOICES = [
        (1, _('Level 1 - Basic Support')),
        (2, _('Level 2 - Technical Support')),
        (3, _('Level 3 - Expert Support')),
        (4, _('Level 4 - Senior Expert / Team Lead')),
    ]

    # HelpDesk fields
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        db_index=True
    )
    support_level = models.IntegerField(
        _('support level'),
        choices=SUPPORT_LEVEL_CHOICES,
        null=True,
        blank=True,
        help_text=_('Support level for agents (1-4). Only applicable for support_agent role.')
    )
    department = models.CharField(
        _('department'),
        max_length=100,
        blank=True,
        null=True
    )
    is_agent = models.BooleanField(
        _('is support agent'),
        default=False,
        help_text=_('Whether this user is a support agent')
    )

    # Cloude fields
    two_factor_enabled = models.BooleanField(
        _('two factor enabled'),
        default=False,
        help_text=_('Whether 2FA is enabled for this account')
    )
    storage_quota_mb = models.IntegerField(
        _('storage quota (MB)'),
        default=1024,
        help_text=_('Total storage quota in MB')
    )
    storage_used_mb = models.IntegerField(
        _('storage used (MB)'),
        default=0,
        help_text=_('Current storage usage in MB')
    )

    # Shared profile fields
    phone = models.CharField(
        _('phone'),
        max_length=20,
        blank=True,
        null=True
    )
    user_timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default='Europe/Berlin',
        help_text=_('User timezone for scheduling and display')
    )

    # Microsoft OAuth2 integration
    microsoft_id = models.CharField(
        _('Microsoft ID'),
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    # Approvals (Phase 3) fields
    is_approver = models.BooleanField(
        _('is approver'),
        default=False,
        help_text=_('Whether this user can approve SSH execution requests')
    )

    # HelpDesk extended fields
    location = models.CharField(
        _('location'),
        max_length=100,
        blank=True,
        null=True
    )

    # Address information (for customers)
    street = models.CharField(
        _('street'),
        max_length=200,
        blank=True,
        null=True
    )
    postal_code = models.CharField(
        _('postal code'),
        max_length=10,
        blank=True,
        null=True
    )
    city = models.CharField(
        _('city'),
        max_length=100,
        blank=True,
        null=True
    )
    country = models.CharField(
        _('country'),
        max_length=100,
        blank=True,
        null=True,
        default='Deutschland'
    )

    # Status and metadata
    email_verified = models.BooleanField(
        _('email verified'),
        default=False
    )
    force_password_change = models.BooleanField(
        _('force password change on next login'),
        default=False,
        help_text=_('If True, user must change password on next login')
    )
    last_activity = models.DateTimeField(
        _('last activity'),
        null=True,
        blank=True,
        help_text=_('Last time user was active')
    )
    created_at = models.DateTimeField(
        _('created at'),
        default=timezone.now,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('ABoroOffice User')
        verbose_name_plural = _('ABoroOffice Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_available_features(self):
        """
        Return list of available features based on user's license.

        Features are determined by the active license for this user's organization.
        Default (no active license) includes only core features.

        Returns:
            list: Feature codes available to this user
        """
        from apps.licensing.models import LicenseKey
        from datetime import date

        # Default features for all users
        features = ['core']

        # Check for active licenses in the system
        # Note: This is a simplified implementation
        # In a multi-tenant system, this should check org-specific licenses
        active_licenses = LicenseKey.objects.filter(
            status='active',
            expiry_date__gte=date.today()
        ).first()

        if active_licenses and active_licenses.product:
            # Get features from the product
            product_features = active_licenses.product.features
            if isinstance(product_features, dict):
                features.extend([f for f, enabled in product_features.items() if enabled])
            elif isinstance(product_features, list):
                features.extend(product_features)

        return list(set(features))  # Remove duplicates

    def can_access_feature(self, feature: str) -> bool:
        """
        Check if user can access a specific feature.

        Args:
            feature: Feature code to check (e.g., 'classroom', 'helpdesk_tickets')

        Returns:
            bool: True if feature is available, False otherwise
        """
        available = self.get_available_features()
        return feature in available

    def get_storage_percentage(self) -> float:
        """Get current storage usage as percentage."""
        if self.storage_quota_mb <= 0:
            return 100.0
        return (self.storage_used_mb / self.storage_quota_mb) * 100

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class SystemSettings(models.Model):
    """
    Global system settings for ABoroOffice.
    Singleton pattern - only one instance should exist.
    """

    # General settings
    site_name = models.CharField(
        _('site name'),
        max_length=255,
        default='ABoroOffice'
    )
    site_url = models.URLField(
        _('site URL'),
        default='https://aboro.office'
    )

    # Email settings
    email_backend = models.CharField(
        _('email backend'),
        max_length=255,
        default='django.core.mail.backends.smtp.EmailBackend'
    )
    email_from = models.EmailField(
        _('email from'),
        default='noreply@aboro.office'
    )
    email_host = models.CharField(
        _('email host'),
        max_length=255,
        blank=True
    )
    email_port = models.IntegerField(
        _('email port'),
        default=587
    )
    email_use_tls = models.BooleanField(
        _('use TLS'),
        default=True
    )

    # License settings
    license_key = models.CharField(
        _('license key'),
        max_length=255,
        blank=True,
        help_text=_('Master license key for the system')
    )

    # System status
    maintenance_mode = models.BooleanField(
        _('maintenance mode'),
        default=False
    )
    maintenance_message = models.TextField(
        _('maintenance message'),
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('System Settings')
        verbose_name_plural = _('System Settings')

    def __str__(self):
        return f"System Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of settings."""
        pass
