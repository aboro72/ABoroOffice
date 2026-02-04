"""
Models for the SSH Approval Workflow (Phase 3)
Integrated from dokmbw_web_app with ABoroUser support
"""

import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from apps.core.models import ABoroUser
from django.conf import settings


class ApprovalSettings(models.Model):
    """
    Global settings for the Approval System (Singleton Pattern)
    Only one instance should exist
    """

    # Approval Deadline
    approval_deadline_hours = models.IntegerField(
        default=24,
        help_text=_('Hours until deadline (default: 24)')
    )
    approval_deadline_minutes = models.IntegerField(
        default=15,
        help_text=_('Minutes for final deadline (default: 15 = 07:15)')
    )

    # Reminder Times
    reminder_1_time = models.TimeField(
        default='14:00',
        help_text=_('First reminder time (default: 14:00)')
    )
    reminder_2_time = models.TimeField(
        default='20:00',
        help_text=_('Second reminder time (default: 20:00)')
    )
    reminder_3_time = models.TimeField(
        default='07:00',
        help_text=_('Third/final reminder time next day (default: 07:00)')
    )

    # SSH Execution
    ssh_timeout = models.IntegerField(
        default=900,
        help_text=_('SSH timeout in seconds (default: 900 = 15 min)')
    )

    # Email Settings
    email_from = models.EmailField(
        default='approvals@aboro.office',
        help_text=_('Email address to send from')
    )

    # System Status
    system_active = models.BooleanField(
        default=True,
        help_text=_('System active? (Inactive = no emails/SSH execution)')
    )

    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Last updated by')
    )

    class Meta:
        verbose_name = _('Approval System Settings')
        verbose_name_plural = _('Approval System Settings')

    def __str__(self):
        return '[OK] Approval System Settings (Singleton)'

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


class ServerHealthCheck(models.Model):
    """
    Health Check for servers: SSH connectivity + URL reachability
    Tested before each approval execution
    """

    STATUS_CHOICES = [
        ('healthy', _('Reachable')),
        ('unreachable', _('Unreachable')),
        ('unknown', _('Not tested')),
    ]

    server_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Server name (e.g., "training-02")')
    )
    server_url = models.URLField(
        help_text=_('Server URL for HTTP connectivity check')
    )
    ssh_port = models.IntegerField(
        default=22,
        help_text=_('SSH port for this server')
    )

    # Connectivity Results
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unknown'
    )
    url_reachable = models.BooleanField(
        default=False,
        help_text=_('Is the URL reachable?')
    )
    ssh_reachable = models.BooleanField(
        default=False,
        help_text=_('Is SSH reachable?')
    )

    last_check = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last health check timestamp')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Server Health Check')
        verbose_name_plural = _('Server Health Checks')
        ordering = ['server_name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['server_name']),
        ]

    def __str__(self):
        return f"{self.server_name} - {self.get_status_display()}"

    def is_healthy(self):
        """Is the server healthy and ready for execution?"""
        return self.status == 'healthy'

    def get_status_icon(self):
        """Get status icon/indicator."""
        if self.status == 'healthy':
            return '[OK]'
        elif self.status == 'unreachable':
            return '[FAIL]'
        else:
            return '[UNKNOWN]'


class RatingSchedule(models.Model):
    """
    Scheduling configuration for approval requests per training environment

    Example:
    - display_name: "Training Environment 02"
    - server_url_prefix: "02"
    - ssh_port: 1424
    - weekdays: [0, 1, 2, 3, 4] (Monday-Friday)
    - abruf_zeit: 16:30 (execution time)
    - approval_email_recipients: ["approver@example.com"]
    """

    display_name = models.CharField(
        max_length=255,
        db_index=True,
        default=_('Training Environment'),
        help_text=_('Display name (e.g., "Training Environment 02")')
    )

    server_url_prefix = models.CharField(
        max_length=2,
        default='02',
        help_text=_('Server number for URL (e.g., "02" for https://02.training.de)')
    )

    ssh_port = models.IntegerField(
        default=1425,
        help_text=_('SSH port for this server')
    )

    # Weekdays as JSON: [0, 1, 2, 3, 4] = Mon-Fri
    weekdays = models.JSONField(
        default=list,
        help_text=_('Days of week: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun')
    )

    # Execution time
    abruf_zeit = models.TimeField(
        help_text=_('Execution time (e.g., 16:30)')
    )

    # Active/Inactive
    enabled = models.BooleanField(
        default=True,
        help_text=_('Enable this schedule')
    )

    # Email recipients for approval requests
    approval_email_recipients = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Email addresses for approval requests')
    )

    # Storage location for reports
    storage_location = models.CharField(
        max_length=500,
        blank=True,
        default='/var/www/reports',
        help_text=_('Local path for storing reports')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Rating Schedule')
        verbose_name_plural = _('Rating Schedules')
        ordering = ['display_name']
        indexes = [
            models.Index(fields=['enabled']),
            models.Index(fields=['display_name']),
        ]

    def __str__(self):
        status = '[OK]' if self.enabled else '[INACTIVE]'
        days = self.get_weekdays_display()
        time_str = self.abruf_zeit.strftime('%H:%M')
        return f"{status} {self.display_name} - {days} {time_str}"

    def get_weekdays_display(self):
        """Display weekdays as text."""
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if not self.weekdays:
            return _('No days')
        days = [day_names[i] for i in self.weekdays if 0 <= i < 7]
        return ', '.join(days) if days else _('No days')

    def has_approval_recipients(self):
        """Check if approval email recipients are configured."""
        return bool(self.approval_email_recipients and len(self.approval_email_recipients) > 0)

    def get_approval_recipients_display(self):
        """Display approval recipients as text."""
        if not self.approval_email_recipients:
            return _('Not configured')
        return ', '.join(self.approval_email_recipients)


class Approval(models.Model):
    """
    Model for SSH Script Execution Approvals
    Workflow: pending → approved/rejected → executed
    """

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
    ]

    APPROVAL_METHOD_CHOICES = [
        ('email', _('Email Link')),
        ('gui', _('GUI Button')),
        ('api', _('API')),
    ]

    EXECUTION_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('success', _('Success')),
        ('failed', _('Failed')),
        ('not_executed', _('Not Executed')),
    ]

    # Unique identifier
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text=_('Unique approval token')
    )

    # Server information
    server_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text=_('Server name for approval')
    )
    server_port = models.IntegerField(
        default=1425,
        help_text=_('SSH port')
    )

    # Link to RatingSchedule (optional)
    rating_schedule = models.ForeignKey(
        'RatingSchedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approvals',
        help_text=_('Related rating schedule')
    )

    # Email recipients for this approval
    email_recipients = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Email recipients for this approval')
    )

    # Scheduling information
    scheduled_time = models.DateTimeField(
        help_text=_('Scheduled execution time')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    deadline = models.DateTimeField(
        help_text=_('Approval deadline (07:15 next day)')
    )

    # Approval status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    approved_by = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_('Email, IP address, or "auto"')
    )
    approval_method = models.CharField(
        max_length=20,
        choices=APPROVAL_METHOD_CHOICES,
        null=True,
        blank=True
    )

    # Reminders tracking
    reminder_1_sent = models.BooleanField(
        default=False,
        help_text=_('14:00 reminder sent')
    )
    reminder_1_time = models.CharField(max_length=5, default='14:00')

    reminder_2_sent = models.BooleanField(
        default=False,
        help_text=_('20:00 reminder sent')
    )
    reminder_2_time = models.CharField(max_length=5, default='20:00')

    reminder_3_sent = models.BooleanField(
        default=False,
        help_text=_('07:00+1 day final reminder sent')
    )
    reminder_3_time = models.CharField(max_length=5, default='07:00')

    # SSH Execution
    executed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    execution_status = models.CharField(
        max_length=20,
        choices=EXECUTION_STATUS_CHOICES,
        default='pending'
    )
    execution_output = models.TextField(blank=True)
    execution_error = models.TextField(blank=True)
    execution_exit_code = models.IntegerField(
        null=True,
        blank=True
    )

    # Email tracking
    initial_email_sent = models.BooleanField(default=False)
    final_summary_email_sent = models.BooleanField(default=False)

    # Notes
    notes = models.TextField(blank=True)

    # Archive
    archived = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Approval Request')
        verbose_name_plural = _('Approval Requests')
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['status', 'deadline']),
            models.Index(fields=['server_name', 'created_at']),
        ]

    def __str__(self):
        scheduled_str = self.scheduled_time.strftime('%d.%m.%Y %H:%M')
        return f"{self.server_name} - {scheduled_str} ({self.get_status_display()})"

    def is_expired(self):
        """Check if approval deadline has passed."""
        return timezone.now() > self.deadline and self.status == 'pending'

    def is_approval_window_open(self):
        """Check if approval window is still open."""
        return timezone.now() <= self.deadline and self.status == 'pending'

    def approve(self, approved_by='unknown', method='gui'):
        """Mark this approval as approved."""
        if self.is_approval_window_open():
            self.status = 'approved'
            self.approved_at = timezone.now()
            self.approved_by = approved_by
            self.approval_method = method
            self.save()
            return True
        return False

    def reject(self, reason=''):
        """Mark this approval as rejected."""
        if self.status == 'pending':
            self.status = 'rejected'
            self.notes = reason
            self.save()
            return True
        return False

    def mark_expired(self):
        """Mark this approval as expired."""
        if self.status == 'pending':
            self.status = 'expired'
            self.save()
            return True
        return False

    def mark_executed(self, exit_code=0, output='', error=''):
        """Mark SSH execution as complete."""
        self.executed_at = timezone.now()
        self.execution_exit_code = exit_code
        self.execution_output = output
        self.execution_error = error
        self.execution_status = 'success' if exit_code == 0 else 'failed'
        self.save()

    def user_can_approve(self, user):
        """
        Check if a user is allowed to approve this request.

        Rules:
        - Staff users can always approve.
        - Non-approver users cannot approve.
        - If a rating schedule is attached, approver must be assigned to it.
        - If no schedule is attached, any approver can approve.
        """
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if not getattr(user, 'is_approver', False):
            return False
        if self.rating_schedule_id:
            return user.approval_groups.filter(pk=self.rating_schedule_id).exists()
        return True

    def log_action(
        self,
        action,
        actor_user=None,
        actor_label='',
        method='',
        ip_address=None,
        user_agent='',
        details=None,
    ):
        """Create an audit log entry for this approval."""
        ApprovalAuditLog.objects.create(
            approval=self,
            action=action,
            actor_user=actor_user,
            actor_label=actor_label,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent or '',
            details=details or {},
        )


class ApprovalReminder(models.Model):
    """
    Helper model to track sent reminders
    """

    approval = models.ForeignKey(
        Approval,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    reminder_number = models.IntegerField(
        help_text=_('Reminder 1, 2, or 3')
    )
    reminder_time = models.CharField(
        max_length=5,
        help_text=_('Time sent (14:00, 20:00, 07:00)')
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    recipients = models.TextField(
        help_text=_('Email recipients (JSON format)')
    )

    class Meta:
        verbose_name = _('Approval Reminder')
        verbose_name_plural = _('Approval Reminders')
        unique_together = ('approval', 'reminder_number')
        ordering = ['-sent_at']

    def __str__(self):
        return f"Reminder {self.reminder_number} - {self.approval.server_name}"


class ApprovalAuditLog(models.Model):
    """Audit log for approval workflow actions."""

    ACTION_CHOICES = [
        ('created', _('Created')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
        ('execution_started', _('Execution Started')),
        ('execution_success', _('Execution Success')),
        ('execution_failed', _('Execution Failed')),
        ('email_sent', _('Email Sent')),
    ]

    approval = models.ForeignKey(
        Approval,
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_audit_logs',
    )
    actor_label = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _('Approval Audit Log')
        verbose_name_plural = _('Approval Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['approval', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.action} - {self.approval.server_name} ({self.created_at})"
