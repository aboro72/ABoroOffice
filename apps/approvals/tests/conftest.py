import pytest

from apps.approvals import celery_tasks


@pytest.fixture(autouse=True)
def disable_celery_delays(monkeypatch):
    """
    Prevent Celery tasks from trying to contact a broker during tests.
    Individual tests can override these patches as needed.
    """
    def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(celery_tasks.send_approval_email_task, 'delay', noop)
    monkeypatch.setattr(celery_tasks.execute_ssh_approval_task, 'delay', noop)
    monkeypatch.setattr(celery_tasks.send_approval_confirmed_email_task, 'delay', noop)
    monkeypatch.setattr(celery_tasks.send_approval_rejected_email_task, 'delay', noop)
