from django.apps import apps
from django.utils import timezone
import requests


def execute_workflow(workflow, context: dict | None = None) -> tuple[str, str]:
    context = context or {}
    messages = []
    try:
        for step in workflow.steps.order_by('order'):
            action = step.action_type
            config = step.config or {}
            if action == 'webhook':
                url = config.get('url')
                if not url:
                    messages.append(f"{step.name}: webhook missing url")
                    continue
                payload = config.get('payload') or context
                requests.post(url, json=payload, timeout=15)
                messages.append(f"{step.name}: webhook ok")
                continue
            if action == 'erp_invoice_email':
                invoice_id = config.get('invoice_id') or context.get('invoice_id')
                if not invoice_id:
                    messages.append(f"{step.name}: invoice_id missing")
                    continue
                Invoice = apps.get_model('erp', 'Invoice')
                invoice = Invoice.objects.filter(id=invoice_id).first()
                if not invoice:
                    messages.append(f"{step.name}: invoice not found")
                    continue
                from apps.erp.services.invoice_mail import send_invoice_email as _send_invoice_email
                if _send_invoice_email(invoice):
                    messages.append(f"{step.name}: invoice email sent")
                else:
                    messages.append(f"{step.name}: invoice email failed")
                continue
            if action == 'erp_dunning_email':
                dunning_id = config.get('dunning_id') or context.get('dunning_id')
                if not dunning_id:
                    messages.append(f"{step.name}: dunning_id missing")
                    continue
                Dunning = apps.get_model('erp', 'DunningNotice')
                notice = Dunning.objects.filter(id=dunning_id).first()
                if not notice:
                    messages.append(f"{step.name}: dunning not found")
                    continue
                from apps.erp.services.dunning import send_dunning_email as _send_dunning_email
                if _send_dunning_email(notice):
                    messages.append(f"{step.name}: dunning email sent")
                else:
                    messages.append(f"{step.name}: dunning email failed")
                continue
            messages.append(f"{step.name}: skipped ({action})")
        return 'success', "\n".join(messages)
    except Exception as exc:
        return 'failed', f"{exc}"


def run_workflows_for_action(action_type: str, context: dict | None = None, trigger: str | None = None) -> int:
    context = context or {}
    Workflow = apps.get_model('workflows', 'Workflow')
    WorkflowExecution = apps.get_model('workflows', 'WorkflowExecution')
    workflows = Workflow.objects.filter(is_active=True, steps__action_type=action_type).distinct()
    if trigger:
        workflows = workflows.filter(trigger_type=trigger)
    ran = 0
    for wf in workflows:
        exec_obj = WorkflowExecution.objects.create(
            workflow=wf,
            status='running',
            message='',
        )
        status, message = execute_workflow(wf, context=context)
        exec_obj.status = status
        exec_obj.message = message
        exec_obj.finished_at = timezone.now()
        exec_obj.save(update_fields=['status', 'message', 'finished_at'])
        ran += 1
    return ran


def run_workflows_for_trigger(trigger: str, context: dict | None = None) -> int:
    context = context or {}
    Workflow = apps.get_model('workflows', 'Workflow')
    WorkflowExecution = apps.get_model('workflows', 'WorkflowExecution')
    workflows = Workflow.objects.filter(is_active=True, trigger_type=trigger).distinct()
    ran = 0
    def _matches(filters: dict, ctx: dict) -> bool:
        if not filters:
            return True
        for key, expected in filters.items():
            actual = ctx.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            else:
                if actual != expected:
                    return False
        return True
    for wf in workflows:
        if not _matches(wf.trigger_filters or {}, context):
            continue
        exec_obj = WorkflowExecution.objects.create(
            workflow=wf,
            status='running',
            message='',
        )
        status, message = execute_workflow(wf, context=context)
        exec_obj.status = status
        exec_obj.message = message
        exec_obj.finished_at = timezone.now()
        exec_obj.save(update_fields=['status', 'message', 'finished_at'])
        ran += 1
    return ran
