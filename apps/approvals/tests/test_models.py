from datetime import timedelta, time

import pytest
from django.utils import timezone

from apps.approvals.models import (
    Approval,
    ApprovalSettings,
    RatingSchedule,
)


@pytest.mark.django_db
def test_approval_settings_singleton():
    settings = ApprovalSettings.get_settings()
    assert settings.pk == 1

    settings.email_from = 'updated@example.com'
    settings.save()

    assert ApprovalSettings.objects.count() == 1
    loaded = ApprovalSettings.objects.get(pk=1)
    assert loaded.email_from == 'updated@example.com'


@pytest.mark.django_db
def test_rating_schedule_helpers():
    schedule = RatingSchedule.objects.create(
        display_name='Training 02',
        server_url_prefix='02',
        ssh_port=1425,
        weekdays=[0, 1, 2],
        abruf_zeit=time(16, 30),
        approval_email_recipients=['approver@example.com'],
    )

    assert schedule.get_weekdays_display() == 'Mon, Tue, Wed'
    assert schedule.has_approval_recipients() is True
    assert 'approver@example.com' in schedule.get_approval_recipients_display()


@pytest.mark.django_db
def test_approval_status_methods():
    now = timezone.now()
    approval = Approval.objects.create(
        server_name='test-server',
        server_port=1425,
        scheduled_time=now + timedelta(hours=1),
        deadline=now + timedelta(hours=24),
        email_recipients=['a@example.com'],
    )

    assert approval.is_expired() is False
    assert approval.is_approval_window_open() is True

    assert approval.approve(approved_by='tester', method='gui') is True
    approval.refresh_from_db()
    assert approval.status == 'approved'
    assert approval.approved_by == 'tester'

    # Reject should fail once approved
    assert approval.reject('no') is False


@pytest.mark.django_db
def test_approval_expire_and_execute():
    now = timezone.now()
    approval = Approval.objects.create(
        server_name='expired-server',
        server_port=1425,
        scheduled_time=now - timedelta(hours=2),
        deadline=now - timedelta(hours=1),
        email_recipients=['b@example.com'],
    )

    assert approval.is_expired() is True
    assert approval.mark_expired() is True
    approval.refresh_from_db()
    assert approval.status == 'expired'

    # Mark executed regardless of status (used by task)
    approval.mark_executed(exit_code=0, output='ok', error='')
    approval.refresh_from_db()
    assert approval.execution_status == 'success'
    assert approval.execution_output == 'ok'
