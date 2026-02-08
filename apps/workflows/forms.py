from django import forms
from .models import Workflow, WorkflowStep


class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ['name', 'description', 'is_active', 'trigger_type', 'trigger_filters']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'trigger_type': forms.Select(attrs={'class': 'form-select', 'id': 'triggerType'}),
            'trigger_filters': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'triggerFilters', 'placeholder': '{"status":"won"}'}),
        }


class WorkflowStepForm(forms.ModelForm):
    class Meta:
        model = WorkflowStep
        fields = ['workflow', 'name', 'action_type', 'config', 'order']
        widgets = {
            'workflow': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
