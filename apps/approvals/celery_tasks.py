"""
Celery tasks for the Approvals app
Handles async operations: email sending, SSH execution, health checks, deadline management
"""

import logging
import os
import paramiko
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from celery import shared_task
from celery.utils.log import get_task_logger

from .models import Approval, ApprovalSettings, RatingSchedule, ServerHealthCheck
from .email_service import EmailService

logger = get_task_logger(__name__)

def _get_ssh_config():
    cfg = getattr(settings, 'APPROVALS_SSH', {})
    return {
        'username': cfg.get('USERNAME') or os.getenv('APPROVALS_SSH_USERNAME'),
        'password': cfg.get('PASSWORD') or os.getenv('APPROVALS_SSH_PASSWORD'),
        'key_path': cfg.get('KEY_PATH') or os.getenv('APPROVALS_SSH_KEY_PATH'),
        'hosts': cfg.get('HOSTS', {}),
        'health_username': cfg.get('HEALTH_USERNAME')
        or os.getenv('APPROVALS_SSH_HEALTH_USERNAME')
        or cfg.get('USERNAME')
        or os.getenv('APPROVALS_SSH_USERNAME'),
    }


def _resolve_host(config, server_name):
    return config.get('hosts', {}).get(server_name, server_name)


# ============================================================================
# EMAIL SENDING TASKS (Priority 1)
# ============================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_approval_email_task(self, approval_id):
    """
    Send initial approval request email

    Args:
        approval_id: ID of the Approval object

    Returns:
        dict with success status and details
    """
    try:
        approval = Approval.objects.get(id=approval_id)
        logger.info(f"Sending approval email for approval {approval_id}")

        result = EmailService.send_approval_request_email(approval)

        if result['success']:
            logger.info(f"Approval email sent successfully for approval {approval_id}")
        else:
            logger.warning(f"Approval email failed for approval {approval_id}: {result['message']}")

        return result

    except Approval.DoesNotExist:
        logger.error(f"Approval {approval_id} not found")
        return {
            'success': False,
            'message': f'Approval {approval_id} not found',
            'approval_id': approval_id
        }
    except Exception as exc:
        logger.error(f"Error sending approval email: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_reminder_email_task(self, approval_id, reminder_number):
    """
    Send reminder email (1, 2, or 3)

    Args:
        approval_id: ID of the Approval object
        reminder_number: Which reminder (1, 2, or 3)

    Returns:
        dict with success status and details
    """
    try:
        approval = Approval.objects.get(id=approval_id)

        if reminder_number not in [1, 2, 3]:
            logger.warning(f"Invalid reminder number {reminder_number} for approval {approval_id}")
            return {
                'success': False,
                'message': f'Invalid reminder number: {reminder_number}',
                'approval_id': approval_id
            }

        logger.info(f"Sending reminder {reminder_number} for approval {approval_id}")

        result = EmailService.send_reminder_email(approval, reminder_number)

        if result['success']:
            logger.info(f"Reminder {reminder_number} sent for approval {approval_id}")
        else:
            logger.warning(f"Reminder {reminder_number} failed for approval {approval_id}: {result['message']}")

        return result

    except Approval.DoesNotExist:
        logger.error(f"Approval {approval_id} not found")
        return {
            'success': False,
            'message': f'Approval {approval_id} not found',
            'approval_id': approval_id
        }
    except Exception as exc:
        logger.error(f"Error sending reminder email: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_approval_confirmed_email_task(self, approval_id):
    """
    Send confirmation email when approval is granted

    Args:
        approval_id: ID of the Approval object

    Returns:
        dict with success status and details
    """
    try:
        approval = Approval.objects.get(id=approval_id)
        logger.info(f"Sending approval confirmed email for approval {approval_id}")

        result = EmailService.send_approval_confirmed_email(approval)

        if result['success']:
            logger.info(f"Approval confirmed email sent for approval {approval_id}")
        else:
            logger.warning(f"Approval confirmed email failed: {result['message']}")

        return result

    except Approval.DoesNotExist:
        logger.error(f"Approval {approval_id} not found")
        return {
            'success': False,
            'message': f'Approval {approval_id} not found',
            'approval_id': approval_id
        }
    except Exception as exc:
        logger.error(f"Error sending approval confirmed email: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_approval_rejected_email_task(self, approval_id):
    """
    Send notification when approval is rejected

    Args:
        approval_id: ID of the Approval object

    Returns:
        dict with success status and details
    """
    try:
        approval = Approval.objects.get(id=approval_id)
        logger.info(f"Sending approval rejected email for approval {approval_id}")

        result = EmailService.send_approval_rejected_email(approval)

        if result['success']:
            logger.info(f"Approval rejected email sent for approval {approval_id}")
        else:
            logger.warning(f"Approval rejected email failed: {result['message']}")

        return result

    except Approval.DoesNotExist:
        logger.error(f"Approval {approval_id} not found")
        return {
            'success': False,
            'message': f'Approval {approval_id} not found',
            'approval_id': approval_id
        }
    except Exception as exc:
        logger.error(f"Error sending approval rejected email: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ============================================================================
# SSH EXECUTION TASK
# ============================================================================

@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def execute_ssh_approval_task(self, approval_id):
    """
    Execute SSH command on remote server after approval

    Args:
        approval_id: ID of the Approval object to execute

    Returns:
        dict with execution status and output
    """
    try:
        approval = Approval.objects.get(id=approval_id)

        # Check if approval is actually approved
        if approval.status != 'approved':
            logger.warning(f"Approval {approval_id} not approved (status: {approval.status})")
            return {
                'success': False,
                'message': f'Approval not in approved status (current: {approval.status})',
                'approval_id': approval_id
            }

        # Check server health
        if approval.rating_schedule:
            health = ServerHealthCheck.objects.filter(
                server_name=approval.server_name
            ).first()
            if health and not health.is_healthy():
                logger.warning(f"Server {approval.server_name} is not healthy")
                approval.execution_status = 'failed'
                approval.execution_error = f'Server health check failed: {health.status}'
                approval.save()
                return {
                    'success': False,
                    'message': f'Server {approval.server_name} is not healthy',
                    'approval_id': approval_id
                }

        logger.info(f"Starting SSH execution for approval {approval_id}")
        approval.execution_status = 'in_progress'
        approval._audit_context = {
            'action': 'execution_started',
            'actor_label': 'system',
            'method': 'ssh',
            'details': {'server': approval.server_name},
        }
        approval.save()

        # Get approval settings for SSH timeout
        try:
            settings = ApprovalSettings.objects.get()
            ssh_timeout = settings.ssh_timeout
        except ApprovalSettings.DoesNotExist:
            ssh_timeout = 900  # Default 15 minutes

        # Attempt SSH execution
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to server
            # NOTE: Credentials should be retrieved from secure storage (environment, vault, etc.)
            # For now, this is a template - actual SSH credentials must be configured separately

            ssh_config = _get_ssh_config()
            host = _resolve_host(ssh_config, approval.server_name)
            username = ssh_config.get('username')
            password = ssh_config.get('password')
            key_path = ssh_config.get('key_path')

            if not username:
                raise ValueError('SSH username is not configured')

            connect_kwargs = {
                'hostname': host,
                'port': approval.server_port,
                'username': username,
                'timeout': ssh_timeout,
            }
            if key_path:
                connect_kwargs['pkey'] = paramiko.RSAKey.from_private_key_file(key_path)
            elif password:
                connect_kwargs['password'] = password
            else:
                raise ValueError('SSH credentials are not configured')

            ssh_client.connect(**connect_kwargs)

            # Execute command (dummy for now - should execute actual script)
            stdin, stdout, stderr = ssh_client.exec_command(
                'echo "Approval executed"',
                timeout=ssh_timeout
            )

            # Capture output
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()

            ssh_client.close()

            # Update approval with execution results
            approval.execution_status = 'success' if exit_code == 0 else 'failed'
            approval.execution_output = output
            approval.execution_error = error if error else ''
            approval.execution_exit_code = exit_code
            approval.executed_at = timezone.now()
            approval._audit_context = {
                'action': 'execution_success' if exit_code == 0 else 'execution_failed',
                'actor_label': 'system',
                'method': 'ssh',
                'details': {
                    'server': approval.server_name,
                    'exit_code': exit_code,
                },
            }
            approval.save()

            logger.info(f"SSH execution completed for approval {approval_id} (exit code: {exit_code})")

            return {
                'success': exit_code == 0,
                'message': 'SSH execution completed',
                'approval_id': approval_id,
                'exit_code': exit_code,
                'output': output[:500]  # Return first 500 chars
            }

        except paramiko.AuthenticationException:
            error_msg = 'SSH authentication failed'
            logger.error(f"{error_msg} for approval {approval_id}")
            approval.execution_status = 'failed'
            approval.execution_error = error_msg
            approval._audit_context = {
                'action': 'execution_failed',
                'actor_label': 'system',
                'method': 'ssh',
                'details': {'server': approval.server_name, 'reason': 'auth_failed'},
            }
            approval.save()
            return {
                'success': False,
                'message': error_msg,
                'approval_id': approval_id
            }
        except paramiko.SSHException as ssh_exc:
            error_msg = f'SSH error: {str(ssh_exc)}'
            logger.error(f"{error_msg} for approval {approval_id}")
            approval.execution_status = 'failed'
            approval.execution_error = error_msg
            approval._audit_context = {
                'action': 'execution_failed',
                'actor_label': 'system',
                'method': 'ssh',
                'details': {'server': approval.server_name, 'reason': 'ssh_exception'},
            }
            approval.save()
            raise self.retry(exc=ssh_exc, countdown=300)
        except Exception as exc:
            error_msg = f'Execution error: {str(exc)}'
            logger.error(f"{error_msg} for approval {approval_id}")
            approval.execution_status = 'failed'
            approval.execution_error = error_msg
            approval._audit_context = {
                'action': 'execution_failed',
                'actor_label': 'system',
                'method': 'ssh',
                'details': {'server': approval.server_name, 'reason': 'exception'},
            }
            approval.save()
            return {
                'success': False,
                'message': error_msg,
                'approval_id': approval_id
            }

    except Approval.DoesNotExist:
        logger.error(f"Approval {approval_id} not found")
        return {
            'success': False,
            'message': f'Approval {approval_id} not found',
            'approval_id': approval_id
        }
    except Exception as exc:
        logger.error(f"Error executing SSH approval: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


# ============================================================================
# SCHEDULER TASKS (Celery Beat)
# ============================================================================

@shared_task
def check_approval_deadlines():
    """
    Scheduler task to mark expired approvals and send final reminders
    Runs periodically (e.g., every hour)
    """
    logger.info("Checking approval deadlines...")

    try:
        # Find approvals that are past deadline
        expired_approvals = Approval.objects.filter(
            status='pending',
            deadline__lt=timezone.now()
        )

        expired_count = expired_approvals.count()
        if expired_count > 0:
            for approval in expired_approvals:
                approval.status = 'expired'
                approval.notes = f'Auto-expired at {timezone.now()}'
                approval._audit_context = {
                    'action': 'expired',
                    'actor_label': 'system',
                    'method': 'auto',
                    'details': {'reason': 'deadline_passed'},
                }
                approval.save(update_fields=['status', 'notes'])
            logger.info(f"Marked {expired_count} approvals as expired")

        # Find approvals approaching deadline (within 1 hour)
        # This could trigger additional notifications if needed
        approaching = Approval.objects.filter(
            status='pending',
            deadline__gt=timezone.now(),
            deadline__lt=timezone.now() + timedelta(hours=1)
        )

        if approaching.exists():
            logger.info(f"Found {approaching.count()} approvals approaching deadline")

        return {
            'success': True,
            'message': f'Checked deadlines, expired {expired_count}',
            'expired_count': expired_count,
            'approaching_count': approaching.count()
        }

    except Exception as exc:
        logger.error(f"Error checking approval deadlines: {str(exc)}")
        return {
            'success': False,
            'message': f'Error: {str(exc)}'
        }


@shared_task
def check_server_health():
    """
    Scheduler task to check server connectivity and health
    Runs periodically (e.g., every 15 minutes)
    """
    logger.info("Checking server health...")

    try:
        schedules = RatingSchedule.objects.filter(enabled=True)

        if not schedules.exists():
            logger.info("No enabled rating schedules to check")
            return {
                'success': True,
                'message': 'No schedules to check'
            }

        checked_count = 0

        ssh_config = _get_ssh_config()
        username = ssh_config.get('health_username')

        if not username:
            logger.warning("SSH health check username not configured")
            return {
                'success': False,
                'message': 'SSH health check username not configured',
            }

        for schedule in schedules:
            try:
                # Check if server is accessible
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    host = _resolve_host(ssh_config, schedule.server_url_prefix)
                    ssh_client.connect(
                        host,
                        port=schedule.ssh_port,
                        username=username,
                        timeout=5
                    )
                    ssh_client.close()

                    ssh_reachable = True
                except Exception:
                    ssh_reachable = False

                # Update or create health check record
                health, created = ServerHealthCheck.objects.get_or_create(
                    server_name=schedule.display_name,
                    defaults={
                        'server_url': schedule.server_url_prefix,
                        'ssh_port': schedule.ssh_port
                    }
                )

                # Determine overall status
                if ssh_reachable:
                    health.status = 'healthy'
                    health.ssh_reachable = True
                else:
                    health.status = 'unreachable'
                    health.ssh_reachable = False

                health.last_check = timezone.now()
                health.save()

                checked_count += 1

            except Exception as exc:
                logger.warning(f"Error checking server health for {schedule.display_name}: {str(exc)}")

        logger.info(f"Server health check completed for {checked_count} servers")

        return {
            'success': True,
            'message': f'Checked {checked_count} servers',
            'checked_count': checked_count
        }

    except Exception as exc:
        logger.error(f"Error in server health check task: {str(exc)}")
        return {
            'success': False,
            'message': f'Error: {str(exc)}'
        }


# ============================================================================
# PERIODIC TASK SCHEDULING SETUP
# ============================================================================
# Add to settings/base.py:
#
# from celery.schedules import crontab
#
# CELERY_BEAT_SCHEDULE = {
#     'check-approval-deadlines': {
#         'task': 'apps.approvals.celery_tasks.check_approval_deadlines',
#         'schedule': crontab(minute=0),  # Every hour
#     },
#     'check-server-health': {
#         'task': 'apps.approvals.celery_tasks.check_server_health',
#         'schedule': crontab(minute='*/15'),  # Every 15 minutes
#     },
# }
