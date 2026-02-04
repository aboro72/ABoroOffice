from datetime import timedelta

import pytest
from django.utils import timezone

from apps.approvals.models import Approval
from apps.approvals import celery_tasks


@pytest.mark.django_db
def test_signal_on_create_sends_email(monkeypatch):
    called = {}

    def fake_delay(approval_id):
        called['approval_id'] = approval_id

    monkeypatch.setattr(celery_tasks.send_approval_email_task, 'delay', fake_delay)

    approval = Approval.objects.create(
        server_name='signal-create',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    assert called.get('approval_id') == approval.id


@pytest.mark.django_db
def test_signal_on_approve_triggers_tasks(monkeypatch):
    called = {'exec': 0, 'confirm': 0}

    def fake_exec_delay(approval_id):
        called['exec'] += 1

    def fake_confirm_delay(approval_id):
        called['confirm'] += 1

    monkeypatch.setattr(celery_tasks.execute_ssh_approval_task, 'delay', fake_exec_delay)
    monkeypatch.setattr(celery_tasks.send_approval_confirmed_email_task, 'delay', fake_confirm_delay)

    approval = Approval.objects.create(
        server_name='signal-approve',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    approval.status = 'approved'
    approval.save()

    assert called['exec'] == 1
    assert called['confirm'] == 1


@pytest.mark.django_db
def test_signal_on_reject_triggers_task(monkeypatch):
    called = {'reject': 0}

    def fake_reject_delay(approval_id):
        called['reject'] += 1

    monkeypatch.setattr(celery_tasks.send_approval_rejected_email_task, 'delay', fake_reject_delay)

    approval = Approval.objects.create(
        server_name='signal-reject',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    approval.status = 'rejected'
    approval.save()

    assert called['reject'] == 1
