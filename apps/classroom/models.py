"""
Classroom Models for ABoroOffice
Migrated from Pit-Kalendar with ABoroUser integration
"""

from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()


class MobileClassroom(models.Model):
    """Mobile classroom/training room for deployment management"""

    ROOM_TYPE_CHOICES = [
        ('AC', 'AC'),
        ('HP', 'HP'),
    ]

    STATUS_CHOICES = [
        ('auf_lager', 'Auf Lager'),
        ('versandfertig', 'Versandfertig'),
        ('versand_geplant', 'Versand geplant'),
        ('an_standort', 'An Standort'),
        ('gesperrt', 'Gesperrt'),
    ]

    name = models.CharField(max_length=10)  # e.g. AC02, HP16
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='auf_lager'
    )
    current_location = models.CharField(max_length=255, blank=True, null=True)

    # Remarks for issues
    remarks = models.TextField(
        blank=True,
        null=True,
        help_text="Remarks about issues or special status (e.g., Not picked up by DPD)"
    )

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Mobile Classrooms"

    def __str__(self):
        return self.name

    def is_in_stock(self):
        """Check if classroom is in stock at warehouse (returned from location)"""
        return self.status == 'auf_lager'

    def can_ship(self):
        """Check if classroom can be shipped (status is versandfertig)"""
        return self.status == 'versandfertig'

    def is_available_for_deployment(self, start_date, end_date, shipping_date=None, pickup_date=None, exclude_deployment_id=None):
        """
        Check if classroom is available for a time period.

        IMPORTANT: Status-independent! Only time conflicts are checked.
        Status (auf_lager, versand_geplant, etc.) are irrelevant for deployment planning.

        Args:
            start_date: deployment_start
            end_date: deployment_end
            shipping_date: planned shipping date (optional)
            pickup_date: planned pickup date (optional)
            exclude_deployment_id: ID of current deployment (when editing)

        Returns:
            tuple: (is_available: bool, reason: str or None)
        """
        # Check for overlaps with other deployments
        buffer_days = 7  # 1 week buffer between pickup and next shipment

        # Find all deployments of this classroom (except current one if editing)
        deployments = self.deployments.all()
        if exclude_deployment_id:
            deployments = deployments.exclude(pk=exclude_deployment_id)

        for deployment in deployments:
            # Check 1: Time period overlap
            # Conflict if: start_date <= deployment.end_date AND end_date >= deployment.start_date
            if start_date <= deployment.deployment_end and end_date >= deployment.deployment_start:
                return (False, f"Time period overlaps with deployment from {deployment.deployment_start} to {deployment.deployment_end}")

            # Check 2: Buffer conflict (7 days between pickup_date and next shipping_date)
            # Only if pickup_date of old deployment exists and shipping_date of new one is planned
            if deployment.pickup_date and shipping_date:
                # Buffer: deployment.pickup_date + 7 days must not be before shipping_date
                min_shipping_date = deployment.pickup_date + timedelta(days=buffer_days)
                if shipping_date < min_shipping_date:
                    days_needed = (min_shipping_date - shipping_date).days
                    return (False, f"Insufficient buffer after pickup on {deployment.pickup_date} (minimum {buffer_days} days required, {days_needed} day(s) too early)")

        return (True, None)

    @staticmethod
    def get_available_classrooms(start_date, end_date, shipping_date=None, pickup_date=None, exclude_deployment_id=None):
        """
        Get all available classrooms for a time period.

        IMPORTANT: Status-independent! Only time conflicts matter.
        Status (auf_lager, versand_geplant, an_standort, etc.) are IGNORED.

        Args:
            start_date: deployment_start
            end_date: deployment_end
            shipping_date: planned shipping date (optional)
            pickup_date: planned pickup date (optional)
            exclude_deployment_id: ID of current deployment (when editing)

        Returns:
            QuerySet of available MobileClassroom objects (sorted by name)
        """
        # Start with ALL classrooms (except 'gesperrt')
        # Status is irrelevant - only time availability matters!
        available_classrooms = MobileClassroom.objects.exclude(
            status='gesperrt'
        ).order_by('name')

        # Filter manually with is_available_for_deployment (time check)
        result = []
        for classroom in available_classrooms:
            is_available, _ = classroom.is_available_for_deployment(
                start_date, end_date, shipping_date, pickup_date, exclude_deployment_id
            )
            if is_available:
                result.append(classroom.pk)

        # Return only available classrooms (as QuerySet for performance)
        return MobileClassroom.objects.filter(pk__in=result).order_by('name')

    @staticmethod
    def get_suggested_classroom(start_date, end_date, shipping_date=None, pickup_date=None, exclude_deployment_id=None):
        """
        Get the next available classroom automatically.

        Priority:
        1. Prefer HP classrooms (HP01, HP02, ..., HP16)
        2. AC classrooms only if no HP available

        User can always change this manually.

        Args:
            start_date: deployment_start
            end_date: deployment_end
            shipping_date: planned shipping date (optional)
            pickup_date: planned pickup date (optional)
            exclude_deployment_id: ID of current deployment (when editing)

        Returns:
            MobileClassroom or None if no available classroom exists
        """
        available = MobileClassroom.get_available_classrooms(
            start_date, end_date, shipping_date, pickup_date, exclude_deployment_id
        )

        # Strategy: Prefer HP, then AC
        # Separate by room type
        hp_rooms = [c for c in available if c.room_type == 'HP']
        ac_rooms = [c for c in available if c.room_type == 'AC']

        # Sort alphabetically
        if hp_rooms:
            hp_rooms.sort(key=lambda x: x.name)
            return hp_rooms[0]
        elif ac_rooms:
            ac_rooms.sort(key=lambda x: x.name)
            return ac_rooms[0]
        else:
            return None


class EmailReminder(models.Model):
    """Email reminders for deployments (shipping and pickup)"""

    REMINDER_TYPE_CHOICES = [
        ('versand', 'Shipping'),
        ('abholung', 'Pickup'),
    ]

    classroom = models.ForeignKey(
        MobileClassroom,
        on_delete=models.CASCADE,
        related_name='email_reminders'
    )
    deployment = models.ForeignKey(
        'ClassroomDeployment',
        on_delete=models.CASCADE,
        related_name='email_reminders',
        null=True,
        blank=True,
        help_text="Deployment for which this reminder was created"
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPE_CHOICES
    )
    send_date = models.DateTimeField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['send_date']
        unique_together = ['deployment', 'reminder_type', 'send_date']

    def __str__(self):
        return f"{self.classroom.name} - {self.get_reminder_type_display()} ({self.send_date})"


class Warehouse(models.Model):
    """Main warehouse - sender address for all shipments"""

    name = models.CharField(max_length=255)  # e.g. "ML Consulting"
    company_name = models.CharField(max_length=255)  # Full company name
    street = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Warehouses"
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} - {self.postal_code} {self.city}"

    def get_formatted_address(self):
        """Get formatted address for display/API"""
        lines = [self.company_name, self.street, self.postal_code, self.city]
        return '\n'.join(line for line in lines if line)


class ShippingAddress(models.Model):
    """Shipping and pickup addresses - deployment sites and current locations"""

    LOCATION_TYPE = [
        ('training', 'Training Site'),
        ('warehouse', 'Warehouse'),
    ]

    name = models.CharField(max_length=255)  # e.g. "Training Center Munich"
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE, default='training')
    street = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Shipping Addresses"

    def __str__(self):
        return f"{self.name} - {self.postal_code} {self.city}"

    def get_formatted_address(self):
        """Get formatted address for display/API"""
        lines = [self.name]
        if self.contact_person:
            lines.append(self.contact_person)
        lines.extend([self.street, self.postal_code, self.city])
        return '\n'.join(line for line in lines if line)


class ClassroomDeployment(models.Model):
    """Deployment planning for classrooms at various locations"""

    classroom = models.ForeignKey(
        MobileClassroom,
        on_delete=models.CASCADE,
        related_name='deployments'
    )
    location = models.ForeignKey(
        ShippingAddress,
        on_delete=models.PROTECT,
        help_text="Deployment site (training center or other location)"
    )

    # Deployment time period
    deployment_start = models.DateField()
    deployment_end = models.DateField()

    # Shipping and pickup dates for this deployment
    shipping_date = models.DateField(blank=True, null=True)
    pickup_date = models.DateField(blank=True, null=True)

    # Confirmation of return
    confirmed_return = models.BooleanField(
        default=False,
        help_text="Confirmed that the classroom returns from the deployment location"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deployment_start']
        verbose_name_plural = "Classroom Deployments"
        unique_together = ['classroom', 'deployment_start', 'deployment_end']

    def __str__(self):
        return f"{self.classroom.name} @ {self.location.name} ({self.deployment_start} - {self.deployment_end})"

    def is_in_deployment(self):
        """Check if classroom is currently in deployment"""
        today = timezone.now().date()
        return self.deployment_start <= today <= self.deployment_end


class DeploymentHistory(models.Model):
    """Complete audit trail for deployment lifecycle"""

    EVENT_TYPE_CHOICES = [
        ('versand_geplant', 'Shipping planned'),
        ('versendet', 'Shipped'),
        ('abholung_geplant', 'Pickup planned'),
        ('zurueckgekommen', 'Returned'),
    ]

    deployment = models.ForeignKey(
        ClassroomDeployment,
        on_delete=models.CASCADE,
        related_name='history_entries',
        help_text="Associated deployment"
    )
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPE_CHOICES,
        help_text="Type of event"
    )
    event_date = models.DateTimeField(
        help_text="Date and time of the event"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deployment_actions',
        help_text="User who performed the action"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional remarks or details"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_date']
        verbose_name = "Deployment History Entry"
        verbose_name_plural = "Deployment History Entries"
        indexes = [
            models.Index(fields=['deployment', '-event_date']),
            models.Index(fields=['event_type', 'event_date']),
        ]

    def __str__(self):
        return f"{self.deployment.classroom.name} - {self.get_event_type_display()} ({self.event_date.strftime('%d.%m.%Y %H:%M')})"


class ChecklistTemplate(models.Model):
    """Template for checklists (AC, HP, both)"""

    ROOM_TYPE_CHOICES = [
        ('AC', 'AC Classrooms'),
        ('HP', 'HP Classrooms'),
        ('both', 'Both (AC & HP)'),
    ]

    name = models.CharField(
        max_length=255,
        help_text="Name of the checklist (e.g., 'Technical Inspection AC')"
    )
    room_type = models.CharField(
        max_length=10,
        choices=ROOM_TYPE_CHOICES,
        help_text="For which classroom types does this checklist apply?"
    )
    description = models.TextField(
        blank=True,
        help_text="Description or instructions for the checklist"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive checklists are not displayed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_type', 'name']
        verbose_name = "Checklist Template"
        verbose_name_plural = "Checklist Templates"

    def __str__(self):
        return self.name


class ChecklistItem(models.Model):
    """Individual items of a checklist template"""

    FIELD_TYPE_CHOICES = [
        ('checkbox', 'Simple checkbox'),
        ('soll_ist', 'Soll/Ist fields (e.g., 3 expected, 2 present)'),
        ('multi_check', 'Multiple checkboxes (e.g., Reset, Updates, Adopted)'),
    ]

    template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.CASCADE,
        related_name='items'
    )
    title = models.CharField(
        max_length=255,
        help_text="Title of the checklist item"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description or instructions"
    )
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default='checkbox',
        help_text="What type of input field should be displayed?"
    )
    soll_label = models.CharField(
        max_length=100,
        blank=True,
        default='Soll',
        help_text="Label for Soll field (only for soll_ist)"
    )
    soll_value = models.CharField(
        max_length=255,
        blank=True,
        help_text="The Soll value (e.g., '13', '4,5,6,7,8', 'D1, D2, 1, 2, 3')"
    )
    ist_label = models.CharField(
        max_length=100,
        blank=True,
        default='Ist',
        help_text="Label for Ist field (only for soll_ist)"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Sort order"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['template', 'order']
        verbose_name = "Checklist Item"
        verbose_name_plural = "Checklist Items"
        unique_together = ['template', 'order']

    def __str__(self):
        return f"{self.template.name} - {self.title}"


class ChecklistItemOption(models.Model):
    """Options for multi_check items (e.g., Reset, Updates, Adopted)"""

    item = models.ForeignKey(
        ChecklistItem,
        on_delete=models.CASCADE,
        related_name='options'
    )
    label = models.CharField(
        max_length=100,
        help_text="Name of the option (e.g., 'Reset')"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Sort order"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['item', 'order']
        verbose_name = "Checklist Item Option"
        verbose_name_plural = "Checklist Item Options"
        unique_together = ['item', 'order']

    def __str__(self):
        return f"{self.item.title} - {self.label}"


class ChecklistCompletion(models.Model):
    """Record of completed checklists"""

    classroom = models.ForeignKey(
        MobileClassroom,
        on_delete=models.CASCADE,
        related_name='checklist_completions'
    )
    template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.PROTECT,
        related_name='completions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='checklist_completions'
    )

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']
        verbose_name = "Checklist Completion"
        verbose_name_plural = "Checklist Completions"
        unique_together = ['classroom', 'template']
        indexes = [
            models.Index(fields=['classroom', 'template']),
            models.Index(fields=['-completed_at']),
        ]

    def __str__(self):
        return f"{self.classroom.name} - {self.template.name} ({self.completed_at.strftime('%d.%m.%Y')})"


class ChecklistItemCompletion(models.Model):
    """Record for individual checklist items (optional for detailed storage)"""

    completion = models.ForeignKey(
        ChecklistCompletion,
        on_delete=models.CASCADE,
        related_name='item_completions'
    )
    item = models.ForeignKey(
        ChecklistItem,
        on_delete=models.PROTECT
    )
    is_completed = models.BooleanField(
        default=True,
        help_text="For checkbox and multi_check items"
    )
    soll_value = models.CharField(
        max_length=255,
        blank=True,
        help_text="Soll value for soll_ist items (e.g., '3')"
    )
    ist_value = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ist value for soll_ist items (e.g., '2')"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes for the item"
    )

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completion', 'item__order']
        verbose_name = "Checklist Item Completion"
        verbose_name_plural = "Checklist Item Completions"
        unique_together = ['completion', 'item']

    def __str__(self):
        status = "✓" if self.is_completed else "✗"
        return f"{status} {self.item.title}"


class ChecklistItemOptionCompletion(models.Model):
    """Record for multi-check options (e.g., Reset, Updates, Adopted)"""

    item_completion = models.ForeignKey(
        ChecklistItemCompletion,
        on_delete=models.CASCADE,
        related_name='option_completions'
    )
    option = models.ForeignKey(
        ChecklistItemOption,
        on_delete=models.CASCADE
    )
    is_checked = models.BooleanField(
        default=False,
        help_text="Whether this option was checked"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['item_completion', 'option__order']
        verbose_name = "Checklist Item Option Completion"
        verbose_name_plural = "Checklist Item Option Completions"
        unique_together = ['item_completion', 'option']

    def __str__(self):
        status = "✓" if self.is_checked else "○"
        return f"{status} {self.option.label}"
