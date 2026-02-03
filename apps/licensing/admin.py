"""
Admin configuration for licensing app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import LicenseProduct, LicenseKey


@admin.register(LicenseProduct)
class LicenseProductAdmin(admin.ModelAdmin):
    """Admin interface for LicenseProduct model."""

    fieldsets = (
        (_('Product Info'), {
            'fields': ('code', 'name', 'tier', 'description', 'is_active')
        }),
        (_('Pricing'), {
            'fields': ('monthly_price', 'yearly_price')
        }),
        (_('Feature Limits'), {
            'fields': ('max_staff_users', 'max_total_users', 'storage_quota_gb')
        }),
        (_('Features'), {
            'fields': ('features',),
            'classes': ('wide',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    list_display = ('code', 'name', 'tier', 'monthly_price', 'max_staff_users', 'status_badge', 'created_at')
    list_filter = ('tier', 'is_active', 'created_at')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('tier', 'code')

    def status_badge(self, obj):
        """Display active status as a colored badge."""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactive</span>'
        )
    status_badge.short_description = _('Status')


@admin.register(LicenseKey)
class LicenseKeyAdmin(admin.ModelAdmin):
    """Admin interface for LicenseKey model."""

    fieldsets = (
        (_('License Identity'), {
            'fields': ('license_code', 'product')
        }),
        (_('Customer Info'), {
            'fields': ('customer_name', 'customer_email')
        }),
        (_('Validity'), {
            'fields': ('issue_date', 'expiry_date', 'status')
        }),
        (_('Deployment'), {
            'fields': ('instance_count',)
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('wide',)
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    list_display = (
        'truncated_code',
        'customer_name',
        'product',
        'status_badge',
        'expiry_date',
        'days_until_expiry',
        'created_at'
    )
    list_filter = ('status', 'product__tier', 'expiry_date', 'created_at')
    search_fields = ('license_code', 'customer_name', 'customer_email')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    ordering = ('-issue_date',)

    def truncated_code(self, obj):
        """Display truncated license code."""
        return f"{obj.license_code[:20]}..."
    truncated_code.short_description = _('License Code')

    def status_badge(self, obj):
        """Display status as a colored badge."""
        color_map = {
            'active': 'green',
            'inactive': 'gray',
            'expired': 'red',
            'suspended': 'orange',
            'revoked': 'darkred',
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{obj.get_status_display()}</span>'
        )
    status_badge.short_description = _('Status')

    def days_until_expiry(self, obj):
        """Display days until expiry with color coding."""
        days = obj.days_until_expiry()
        if days < 0:
            color = 'red'
            text = f"{abs(days)} days ago"
        elif days < 30:
            color = 'orange'
            text = f"{days} days"
        else:
            color = 'green'
            text = f"{days} days"

        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{text}</span>'
        )
    days_until_expiry.short_description = _('Days Until Expiry')

    def save_model(self, request, obj, form, change):
        """Auto-set created_by on creation."""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
