from django.db import models
from django.conf import settings


class Project(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('done', 'Done'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    crm_account = models.ForeignKey('crm.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    crm_opportunity = models.ForeignKey('crm.Opportunity', on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    erp_quote = models.ForeignKey('erp.Quote', on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    erp_order = models.ForeignKey('erp.SalesOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    wip_limit_todo = models.PositiveIntegerField(null=True, blank=True)
    wip_limit_in_progress = models.PositiveIntegerField(null=True, blank=True)
    wip_limit_blocked = models.PositiveIntegerField(null=True, blank=True)
    wip_limit_done = models.PositiveIntegerField(null=True, blank=True)
    wip_limit_assignee = models.PositiveIntegerField(null=True, blank=True)
    wip_limit_team = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Milestone(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('done', 'Done'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')

    def __str__(self):
        return f"{self.project.name}: {self.title}"


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked'),
        ('done', 'Done'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.task_id}"
