"""
Admin configuration for classroom app.
"""

from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import (
    MobileClassroom, EmailReminder, ShippingAddress, Warehouse, ClassroomDeployment,
    DeploymentHistory, ChecklistTemplate, ChecklistItem, ChecklistCompletion,
    ChecklistItemCompletion, ChecklistItemOption, ChecklistItemOptionCompletion
)


@admin.register(MobileClassroom)
class MobileClassroomAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'room_type',
        'status_badge',
        'current_location'
    ]
    list_filter = ['status', 'room_type']
    search_fields = ['name', 'current_location']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_in_stock', 'mark_ready_to_ship', 'mark_on_location']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'room_type', 'status', 'current_location')
        }),
        ('Remarks', {
            'fields': ('remarks',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'auf_lager': '#27ae60',
            'versandfertig': '#f39c12',
            'versand_geplant': '#e67e22',
            'an_standort': '#3498db',
            'gesperrt': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def mark_in_stock(self, request, queryset):
        updated = queryset.update(status='auf_lager')
        self.message_user(request, f'{updated} classrooms marked as "In Stock".')
    mark_in_stock.short_description = 'Mark as "In Stock"'

    def mark_ready_to_ship(self, request, queryset):
        updated = queryset.update(status='versandfertig')
        self.message_user(request, f'{updated} classrooms marked as "Ready to Ship".')
    mark_ready_to_ship.short_description = 'Mark as "Ready to Ship"'

    def mark_on_location(self, request, queryset):
        updated = queryset.update(status='an_standort')
        self.message_user(request, f'{updated} classrooms marked as "On Location".')
    mark_on_location.short_description = 'Mark as "On Location"'


@admin.register(EmailReminder)
class EmailReminderAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'reminder_type', 'send_date', 'sent_status', 'sent_at']
    list_filter = ['reminder_type', 'sent', 'send_date']
    search_fields = ['classroom__name']
    readonly_fields = ['created_at', 'updated_at', 'sent_at']

    def sent_status(self, obj):
        if obj.sent:
            return mark_safe('<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px;">✓ Sent</span>')
        else:
            return mark_safe('<span style="background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 3px;">○ Pending</span>')
    sent_status.short_description = 'Status'


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'company_name', 'postal_code', 'city', 'is_active_badge']
    list_filter = ['is_active', 'city']
    search_fields = ['name', 'company_name', 'city', 'postal_code']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company_name', 'is_active')
        }),
        ('Address', {
            'fields': ('street', 'postal_code', 'city')
        }),
        ('Contact', {
            'fields': ('phone', 'email'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['name', 'location_type', 'postal_code', 'city', 'is_active_badge']
    list_filter = ['location_type', 'is_active', 'city']
    search_fields = ['name', 'city', 'postal_code', 'contact_person']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location_type', 'is_active')
        }),
        ('Address', {
            'fields': ('street', 'postal_code', 'city')
        }),
        ('Contact', {
            'fields': ('contact_person', 'phone', 'email'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'


@admin.register(ClassroomDeployment)
class ClassroomDeploymentAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'location', 'deployment_start', 'deployment_end', 'shipping_status', 'is_in_deployment_badge']
    list_filter = ['deployment_start', 'deployment_end', 'classroom__room_type']
    search_fields = ['classroom__name', 'location__name']
    readonly_fields = ['created_at', 'updated_at', 'is_in_deployment_badge']
    date_hierarchy = 'deployment_start'

    fieldsets = (
        ('Deployment Information', {
            'fields': ('classroom', 'location', 'is_in_deployment_badge')
        }),
        ('Deployment Period', {
            'fields': ('deployment_start', 'deployment_end')
        }),
        ('Shipping & Pickup', {
            'fields': ('shipping_date', 'pickup_date', 'confirmed_return')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def shipping_status(self, obj):
        if obj.shipping_date and obj.pickup_date:
            return format_html('<span style="color: green;">✓ Shipped & Returned</span>')
        elif obj.shipping_date:
            return format_html('<span style="color: orange;">○ Shipped, awaiting return</span>')
        else:
            return format_html('<span style="color: gray;">○ Pending</span>')
    shipping_status.short_description = 'Shipping Status'

    def is_in_deployment_badge(self, obj):
        if obj.is_in_deployment():
            return format_html('<span style="color: green; font-weight: bold;">✓ Currently Deployed</span>')
        return format_html('<span style="color: gray;">○ Not Currently Deployed</span>')
    is_in_deployment_badge.short_description = 'Current Status'


@admin.register(DeploymentHistory)
class DeploymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['deployment', 'event_type', 'event_date', 'user']
    list_filter = ['event_type', 'event_date']
    search_fields = ['deployment__classroom__name', 'user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'event_date'

    fieldsets = (
        ('Event Information', {
            'fields': ('deployment', 'event_type', 'event_date', 'user')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'is_active_badge', 'item_count']
    list_filter = ['room_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'item_count']

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'room_type', 'is_active', 'item_count')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'

    def item_count(self, obj):
        count = obj.items.count()
        return format_html(f'<strong>{count}</strong> items')
    item_count.short_description = 'Items'


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'template', 'field_type', 'order']
    list_filter = ['template__room_type', 'field_type']
    search_fields = ['title', 'template__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['template', 'order']

    fieldsets = (
        ('Item Information', {
            'fields': ('template', 'title', 'order')
        }),
        ('Field Configuration', {
            'fields': ('field_type', 'soll_label', 'soll_value', 'ist_label')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChecklistCompletion)
class ChecklistCompletionAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'template', 'user', 'completed_at']
    list_filter = ['template__room_type', 'completed_at']
    search_fields = ['classroom__name', 'user__email']
    readonly_fields = ['completed_at']
    date_hierarchy = 'completed_at'

    fieldsets = (
        ('Completion Information', {
            'fields': ('classroom', 'template', 'user', 'completed_at')
        }),
    )
