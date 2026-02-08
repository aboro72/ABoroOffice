from django import forms
from .models import Project, Task, Milestone, TaskComment


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'status',
            'start_date',
            'due_date',
            'owner',
            'crm_account',
            'crm_opportunity',
            'erp_quote',
            'erp_order',
            'wip_limit_todo',
            'wip_limit_in_progress',
            'wip_limit_blocked',
            'wip_limit_done',
            'wip_limit_assignee',
            'wip_limit_team',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'crm_account': forms.Select(attrs={'class': 'form-select'}),
            'crm_opportunity': forms.Select(attrs={'class': 'form-select'}),
            'erp_quote': forms.Select(attrs={'class': 'form-select'}),
            'erp_order': forms.Select(attrs={'class': 'form-select'}),
            'wip_limit_todo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'wip_limit_in_progress': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'wip_limit_blocked': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'wip_limit_done': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'wip_limit_assignee': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'wip_limit_team': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['project', 'title', 'due_date', 'status']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['project', 'milestone', 'title', 'description', 'status', 'priority', 'assignee', 'due_date']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'milestone': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
