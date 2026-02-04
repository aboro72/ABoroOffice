from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.approvals.models import Approval
from apps.approvals.models import ServerHealthCheck, RatingSchedule
from apps.core.models import ABoroUser


@pytest.mark.django_db
def test_approval_list_requires_login(client):
    response = client.get('/approvals/')
    assert response.status_code == 302
    assert '/admin/login/' in response['Location']


@pytest.mark.django_db
def test_approval_list_and_detail_views(client):
    user = ABoroUser.objects.create_user(
        username='viewer',
        email='viewer@example.com',
        password='pass1234',
    )
    client.login(username='viewer', password='pass1234')

    approval = Approval.objects.create(
        server_name='list-server',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    response = client.get('/approvals/')
    assert response.status_code == 200
    assert b'SSH Approvals' in response.content

    detail = client.get(f'/approvals/{approval.token}/')
    assert detail.status_code == 200


@pytest.mark.django_db
def test_approve_via_token_no_login(client):
    approval = Approval.objects.create(
        server_name='token-server',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )

    response = client.post(f'/approvals/{approval.token}/approve/')
    assert response.status_code == 302

    approval.refresh_from_db()
    assert approval.status == 'approved'
    assert approval.approval_method == 'email'


@pytest.mark.django_db
def test_reject_requires_approver(client):
    user = ABoroUser.objects.create_user(
        username='approver',
        email='approver@example.com',
        password='pass1234',
        is_approver=True,
    )
    client.login(username='approver', password='pass1234')

    schedule = RatingSchedule.objects.create(
        display_name='Training 99',
        server_url_prefix='99',
        ssh_port=1425,
        weekdays=[0, 1],
        abruf_zeit=timezone.now().time(),
        approval_email_recipients=['approver@example.com'],
    )
    user.approval_groups.add(schedule)

    approval = Approval.objects.create(
        server_name='reject-server',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
        rating_schedule=schedule,
    )

    response = client.post(f'/approvals/approval/{approval.pk}/reject/', data={'reason': 'No'})
    assert response.status_code in [200, 302]

    approval.refresh_from_db()
    assert approval.status == 'rejected'


@pytest.mark.django_db
def test_health_and_statistics_endpoints(client):
    user = ABoroUser.objects.create_user(
        username='stats',
        email='stats@example.com',
        password='pass1234',
        is_approver=True,
    )
    client.login(username='stats', password='pass1234')

    Approval.objects.create(
        server_name='stat-server',
        server_port=1425,
        scheduled_time=timezone.now() + timedelta(hours=1),
        deadline=timezone.now() + timedelta(hours=24),
        email_recipients=['approver@example.com'],
    )
    ServerHealthCheck.objects.create(
        server_name='health-server',
        server_url='https://example.com',
        ssh_port=22,
        status='healthy',
        ssh_reachable=True,
        url_reachable=True,
        last_check=timezone.now(),
    )
    RatingSchedule.objects.create(
        display_name='Training 01',
        server_url_prefix='01',
        ssh_port=1425,
        weekdays=[0, 1],
        abruf_zeit=timezone.now().time(),
        approval_email_recipients=['approver@example.com'],
    )

    health_response = client.get('/approvals/health/')
    assert health_response.status_code == 200
    assert health_response.json()['success'] is True

    stats_response = client.get('/approvals/statistics/')
    assert stats_response.status_code == 200
    assert stats_response.json()['success'] is True

    schedule_response = client.get('/approvals/schedule/')
    assert schedule_response.status_code == 200
    assert schedule_response.json()['success'] is True
