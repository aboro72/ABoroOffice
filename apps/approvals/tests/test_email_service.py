from datetime import timedelta

import pytest
from django.core import mail
from django.test import override_settings
from django.utils import timezone

from apps.approvals.email_service import EmailService
from apps.approvals.models import Approval


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@example.com',
    SITE_URL='http://testserver',
)
def test_email_service_sends_request_and_reminders():
    approval = Approval.objects.create(
        server_name='mail-server',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    result = EmailService.send_approval_request_email(approval)
    assert result['success'] is True
    assert approval.initial_email_sent is True
    assert len(mail.outbox) == 1

    reminder_result = EmailService.send_reminder_email(approval, 1)
    assert reminder_result['success'] is True
    approval.refresh_from_db()
    assert approval.reminder_1_sent is True
    assert len(mail.outbox) == 2


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@example.com',
)
def test_email_service_confirm_and_reject():
    approval = Approval.objects.create(
        server_name='mail-server-2',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
        status='approved',
        approved_by='tester@example.com',
    )

    confirm = EmailService.send_approval_confirmed_email(approval)
    assert confirm['success'] is True
    assert len(mail.outbox) == 1

    approval.status = 'rejected'
    approval.notes = 'Not allowed'
    approval.save()
    reject = EmailService.send_approval_rejected_email(approval)
    assert reject['success'] is True
    assert len(mail.outbox) == 2
