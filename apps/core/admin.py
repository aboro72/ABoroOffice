"""
Admin configuration for core app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import ABoroUser, SystemSettings


@admin.register(ABoroUser)
class ABoroUserAdmin(BaseUserAdmin):
    """Admin interface for ABoroUser model."""

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'phone', 'timezone')
        }),
        (_('HelpDesk'), {
            'fields': ('role', 'support_level', 'department', 'is_agent', 'location'),
            'classes': ('collapse',)
        }),
        (_('Cloude'), {
            'fields': ('two_factor_enabled', 'storage_quota_mb', 'storage_used_mb'),
            'classes': ('collapse',)
        }),
        (_('Approvals'), {
            'fields': ('is_approver',),
            'classes': ('collapse',)
        }),
        (_('Address'), {
            'fields': ('street', 'postal_code', 'city', 'country'),
            'classes': ('collapse',)
        }),
        (_('OAuth'), {
            'fields': ('microsoft_id',),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
        (_('Account Security'), {
            'fields': ('email_verified', 'force_password_change'),
            'classes': ('collapse',)
        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_approver', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_approver', 'role', 'is_agent', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'last_activity')
    ordering = ('-created_at',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin interface for SystemSettings model."""

    fieldsets = (
        (_('General'), {
            'fields': ('site_name', 'site_url')
        }),
        (_('Email Settings'), {
            'fields': (
                'email_backend',
                'email_from',
                'email_host',
                'email_port',
                'email_use_tls'
            ),
            'classes': ('collapse',)
        }),
        (_('License'), {
            'fields': ('license_key',),
            'classes': ('collapse',)
        }),
        (_('Maintenance'), {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        """Prevent creating new settings instances."""
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting settings."""
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect to the single settings object."""
        settings_obj = SystemSettings.get_settings()
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(reverse('admin:core_systemsettings_change', args=[settings_obj.pk]))
