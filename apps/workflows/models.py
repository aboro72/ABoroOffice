from django.db import models


class Workflow(models.Model):
    TRIGGER_CHOICES = [
        ('manual', 'Manual'),
        ('invoice_issued', 'Invoice Issued'),
        ('dunning_created', 'Dunning Created'),
        ('erp_order_status', 'ERP Order Status Changed'),
        ('crm_lead_status', 'CRM Lead Status Changed'),
        ('crm_opportunity_stage', 'CRM Opportunity Stage Changed'),
        ('marketing_asset_status', 'Marketing Asset Status Changed'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    trigger_type = models.CharField(max_length=40, choices=TRIGGER_CHOICES, default='manual')
    trigger_filters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    ACTION_CHOICES = [
        ('email', 'Send Email'),
        ('webhook', 'Webhook Call'),
        ('erp_update', 'ERP Update'),
        ('erp_invoice_email', 'ERP Invoice Email'),
        ('erp_dunning_email', 'ERP Dunning Email'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=200)
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES, default='email')
    config = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.workflow.name}: {self.name}"


class WorkflowExecution(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.workflow.name} ({self.status})"
