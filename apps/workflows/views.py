from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .models import Workflow, WorkflowStep, WorkflowExecution
from .forms import WorkflowForm, WorkflowStepForm
from .services import execute_workflow


class WorkflowHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'workflows/home.html'


class WorkflowHelpView(LoginRequiredMixin, TemplateView):
    template_name = 'workflows/help.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow_count'] = Workflow.objects.count()
        context['active_workflows'] = Workflow.objects.filter(is_active=True).count()
        context['execution_count'] = WorkflowExecution.objects.count()
        return context


class WorkflowListView(LoginRequiredMixin, ListView):
    model = Workflow
    template_name = 'workflows/workflow_list.html'
    context_object_name = 'workflows'


class WorkflowCreateView(LoginRequiredMixin, CreateView):
    model = Workflow
    form_class = WorkflowForm
    template_name = 'workflows/form.html'
    success_url = reverse_lazy('workflows:workflow_list')


class WorkflowDetailView(LoginRequiredMixin, DetailView):
    model = Workflow
    template_name = 'workflows/workflow_detail.html'
    context_object_name = 'workflow'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['steps'] = self.object.steps.order_by('order')
        context['executions'] = self.object.executions.order_by('-started_at')[:20]
        context['step_form'] = WorkflowStepForm(initial={'workflow': self.object})
        context['filter_builder_fields'] = [
            ('status', 'Status'),
            ('stage', 'Stage'),
            ('level', 'Level'),
        ]
        context['filter_builder_ops'] = [
            ('eq', '='),
            ('in', 'in'),
        ]
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'add_step' in request.POST:
            form = WorkflowStepForm(request.POST)
            if form.is_valid():
                form.save()
            return redirect('workflows:workflow_detail', pk=self.object.pk)
        if 'add_step_template' in request.POST:
            name = request.POST.get('step_name') or 'Neuer Schritt'
            step_type = request.POST.get('step_type') or 'email'
            config = {}
            if step_type == 'webhook':
                config = {'url': 'https://example.com/webhook'}
            order = (self.object.steps.aggregate(models.Max('order')).get('order__max') or 0) + 1
            WorkflowStep.objects.create(
                workflow=self.object,
                name=name,
                action_type=step_type,
                config=config,
                order=order,
            )
            return redirect('workflows:workflow_detail', pk=self.object.pk)
        if 'save_filters' in request.POST:
            raw = request.POST.get('trigger_filters') or ''
            try:
                data = json.loads(raw) if raw.strip() else {}
                self.object.trigger_filters = data
                self.object.save(update_fields=['trigger_filters'])
                messages.success(request, "Trigger-Filter gespeichert.")
            except Exception as exc:
                messages.error(request, f"Trigger-Filter ungültig: {exc}")
            return redirect('workflows:workflow_detail', pk=self.object.pk)
        if 'validate_filters' in request.POST:
            errors = []
            raw = request.POST.get('trigger_filters') or ''
            try:
                if raw.strip():
                    json.loads(raw)
            except Exception as exc:
                errors.append(str(exc))
            if errors:
                messages.error(request, f"Trigger-Filter JSON ungültig: {errors[0]}")
            else:
                messages.success(request, "Trigger-Filter JSON ist gültig.")
            return redirect('workflows:workflow_detail', pk=self.object.pk)
        if 'run_workflow' in request.POST:
            exec_obj = WorkflowExecution.objects.create(
                workflow=self.object,
                status='running',
                message='',
            )
            context = {}
            invoice_id = request.POST.get('invoice_id')
            dunning_id = request.POST.get('dunning_id')
            if invoice_id:
                context['invoice_id'] = int(invoice_id)
            if dunning_id:
                context['dunning_id'] = int(dunning_id)
            status, message = execute_workflow(self.object, context=context)
            exec_obj.status = status
            exec_obj.message = message
            exec_obj.finished_at = timezone.now()
            exec_obj.save(update_fields=['status', 'message', 'finished_at'])
            return redirect('workflows:workflow_detail', pk=self.object.pk)
        return redirect('workflows:workflow_detail', pk=self.object.pk)
