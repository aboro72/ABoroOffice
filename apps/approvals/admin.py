"""
Django Admin Configuration for Approvals App
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    Approval, ApprovalReminder, ApprovalSettings,
    ServerHealthCheck, RatingSchedule, ApprovalAuditLog
)


@admin.register(ApprovalSettings)
class ApprovalSettingsAdmin(admin.ModelAdmin):
    """Admin for Approval System Settings (Singleton)."""

    fieldsets = (
        (_('Approval Deadlines'), {
            'fields': ('approval_deadline_hours', 'approval_deadline_minutes')
        }),
        (_('Reminder Times'), {
            'fields': ('reminder_1_time', 'reminder_2_time', 'reminder_3_time')
        }),
        (_('SSH Configuration'), {
            'fields': ('ssh_timeout',)
        }),
        (_('Email Settings'), {
            'fields': ('email_from',)
        }),
        (_('System Status'), {
            'fields': ('system_active',)
        }),
        (_('Audit'), {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        """Prevent adding new settings (singleton)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting settings."""
        return False


@admin.register(ServerHealthCheck)
class ServerHealthCheckAdmin(admin.ModelAdmin):
    """Admin for Server Health Checks."""

    list_display = (
        'server_name',
        'status_icon',
        'url_reachable',
        'ssh_reachable',
        'last_check_display'
    )
    list_filter = ('status', 'url_reachable', 'ssh_reachable', 'last_check')
    search_fields = ('server_name', 'server_url')
    readonly_fields = ('created_at', 'updated_at', 'last_check')

    fieldsets = (
        (_('Server Information'), {
            'fields': ('server_name', 'server_url', 'ssh_port')
        }),
        (_('Health Status'), {
            'fields': ('status', 'url_reachable', 'ssh_reachable', 'last_check')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_icon(self, obj):
        """Display status with icon."""
        if obj.status == 'healthy':
            return format_html('<span style="color: green;">&#10003; Healthy</span>')
        elif obj.status == 'unreachable':
            return format_html('<span style="color: red;">&#10005; Unreachable</span>')
        else:
            return format_html('<span style="color: orange;">? Unknown</span>')
    status_icon.short_description = _('Status')

    def last_check_display(self, obj):
        """Display last check time."""
        if obj.last_check:
            return obj.last_check.strftime('%d.%m.%Y %H:%M:%S')
        return '-'
    last_check_display.short_description = _('Last Check')


@admin.register(RatingSchedule)
class RatingScheduleAdmin(admin.ModelAdmin):
    """Admin for Rating Schedule Configuration."""

    list_display = (
        'status_icon',
        'display_name',
        'ssh_port',
        'weekdays_display',
        'abruf_zeit',
        'enabled'
    )
    list_filter = ('enabled', 'ssh_port')
    search_fields = ('display_name', 'server_url_prefix')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (_('Server Configuration'), {
            'fields': ('display_name', 'server_url_prefix', 'ssh_port')
        }),
        (_('Schedule'), {
            'fields': ('weekdays', 'abruf_zeit', 'enabled')
        }),
        (_('Email Recipients'), {
            'fields': ('approval_email_recipients',),
            'description': _('JSON list of email addresses for approvals')
        }),
        (_('Storage'), {
            'fields': ('storage_location',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_icon(self, obj):
        """Display enabled/disabled icon."""
        if obj.enabled:
            return format_html('<span style="color: green;">&#10003;</span>')
        return format_html('<span style="color: red;">&#10005;</span>')
    status_icon.short_description = _('Active')

    def weekdays_display(self, obj):
        """Display weekdays."""
        return obj.get_weekdays_display()
    weekdays_display.short_description = _('Days')


class ApprovalReminderInline(admin.TabularInline):
    """Inline admin for approval reminders."""

    model = ApprovalReminder
    extra = 0
    readonly_fields = ('reminder_number', 'reminder_time', 'sent_at', 'recipients')
    can_delete = False


@admin.register(ApprovalAuditLog)
class ApprovalAuditLogAdmin(admin.ModelAdmin):
    """Admin for Approval Audit Logs."""

    list_display = ('created_at', 'action', 'approval', 'actor_user', 'actor_label', 'method')
    list_filter = ('action', 'method', 'created_at')
    search_fields = ('approval__server_name', 'approval__token', 'actor_label')
    readonly_fields = (
        'approval',
        'action',
        'actor_user',
        'actor_label',
        'method',
        'ip_address',
        'user_agent',
        'details',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    """Admin for Approval Requests."""

    list_display = (
        'status_icon',
        'server_name',
        'scheduled_time_display',
        'status',
        'approved_by_display',
        'execution_status_icon',
        'created_at'
    )
    list_filter = (
        'status',
        'approval_method',
        'execution_status',
        'created_at',
        'approved_at'
    )
    search_fields = ('server_name', 'token', 'approved_by')
    readonly_fields = (
        'token',
        'created_at',
        'approved_at',
        'executed_at',
        'scheduled_time_display'
    )

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('token', 'server_name', 'server_port', 'rating_schedule')
        }),
        (_('Approval Status'), {
            'fields': (
                'status',
                'scheduled_time_display',
                'deadline',
                'approved_at',
                'approved_by',
                'approval_method'
            )
        }),
        (_('Reminders'), {
            'fields': (
                'reminder_1_sent',
                'reminder_2_sent',
                'reminder_3_sent'
            ),
            'classes': ('collapse',)
        }),
        (_('SSH Execution'), {
            'fields': (
                'execution_status',
                'executed_at',
                'execution_exit_code',
                'execution_output',
                'execution_error'
            ),
            'classes': ('collapse',)
        }),
        (_('Email'), {
            'fields': ('email_recipients', 'initial_email_sent', 'final_summary_email_sent'),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    inlines = [ApprovalReminderInline]

    actions = ['mark_approved', 'mark_rejected', 'mark_expired']

    def status_icon(self, obj):
        """Display status icon."""
        icons = {
            'pending': '<span style="color: orange;">&#10229;</span>',
            'approved': '<span style="color: green;">&#10003;</span>',
            'rejected': '<span style="color: red;">&#10005;</span>',
            'expired': '<span style="color: gray;">&#9325;</span>',
        }
        return format_html(icons.get(obj.status, '-'))
    status_icon.short_description = _('Status')

    def scheduled_time_display(self, obj):
        """Display scheduled time in readable format."""
        return obj.scheduled_time.strftime('%d.%m.%Y %H:%M:%S')
    scheduled_time_display.short_description = _('Scheduled Time')

    def approved_by_display(self, obj):
        """Display who approved."""
        if obj.approved_by:
            return f"{obj.approved_by} ({obj.get_approval_method_display()})"
        return '-'
    approved_by_display.short_description = _('Approved By')

    def execution_status_icon(self, obj):
        """Display execution status icon."""
        icons = {
            'pending': '<span style="color: gray;">-</span>',
            'in_progress': '<span style="color: blue;">⟳</span>',
            'success': '<span style="color: green;">✓</span>',
            'failed': '<span style="color: red;">✗</span>',
        }
        return format_html(icons.get(obj.execution_status, '-'))
    execution_status_icon.short_description = _('Execution')

    @admin.action(description=_('Mark selected as approved'))
    def mark_approved(self, request, queryset):
        """Mark selected approvals as approved."""
        count = 0
        for approval in queryset.filter(status='pending'):
            approval.approve(approved_by=request.user.email, method='gui')
            count += 1
        self.message_user(request, f'{count} approval(s) marked as approved')

    @admin.action(description=_('Mark selected as rejected'))
    def mark_rejected(self, request, queryset):
        """Mark selected approvals as rejected."""
        count = 0
        for approval in queryset.filter(status='pending'):
            approval.reject(reason='Rejected via admin')
            count += 1
        self.message_user(request, f'{count} approval(s) marked as rejected')

    @admin.action(description=_('Mark selected as expired'))
    def mark_expired(self, request, queryset):
        """Mark selected approvals as expired."""
        count = 0
        for approval in queryset.filter(status='pending'):
            approval.mark_expired()
            count += 1
        self.message_user(request, f'{count} approval(s) marked as expired')
