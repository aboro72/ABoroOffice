from datetime import timedelta

import pytest
from django.utils import timezone

from apps.approvals import celery_tasks
from apps.approvals.models import Approval


@pytest.mark.django_db
def test_check_approval_deadlines_marks_expired():
    approval = Approval.objects.create(
        server_name='deadline-server',
        server_port=1425,
        scheduled_time=timezone.now() - timedelta(hours=2),
        deadline=timezone.now() - timedelta(hours=1),
        email_recipients=['approver@example.com'],
    )

    result = celery_tasks.check_approval_deadlines()
    approval.refresh_from_db()

    assert result['success'] is True
    assert approval.status == 'expired'


@pytest.mark.django_db
def test_execute_ssh_approval_task_requires_approved():
    approval = Approval.objects.create(
        server_name='exec-server',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    result = celery_tasks.execute_ssh_approval_task(approval.id)
    assert result['success'] is False
    assert 'not approved' in result['message'].lower()


@pytest.mark.django_db
def test_send_reminder_email_task_invalid_number():
    approval = Approval.objects.create(
        server_name='reminder-server',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    result = celery_tasks.send_reminder_email_task(approval.id, 9)
    assert result['success'] is False


@pytest.mark.django_db
def test_send_approval_email_task_uses_service(monkeypatch):
    approval = Approval.objects.create(
        server_name='email-task-server',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    called = {}

    def fake_send(approval_obj):
        called['id'] = approval_obj.id
        return {'success': True, 'message': 'ok', 'approval_id': approval_obj.id}

    monkeypatch.setattr(
        celery_tasks.EmailService,
        'send_approval_request_email',
        fake_send
    )

    result = celery_tasks.send_approval_email_task(approval.id)
    assert result['success'] is True
    assert called.get('id') == approval.id
