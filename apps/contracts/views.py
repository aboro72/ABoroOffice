from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.urls import reverse
from .models import Contract, ContractVersion
from .forms import ContractForm, ContractVersionForm
from .services.ai import analyze_contract
from .exports import export_contract_analysis_docx
from .permissions import ContractsViewMixin, ContractsEditMixin


class ContractListView(ContractsViewMixin, ListView):
    model = Contract
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 50

    def get_queryset(self):
        qs = Contract.objects.all().order_by('-updated_at')
        status = self.request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)
        return qs


class ContractDetailView(ContractsViewMixin, DetailView):
    model = Contract
    template_name = 'contracts/contract_detail.html'
    context_object_name = 'contract'


class ContractCreateView(ContractsEditMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        contract = self.object
        _data, error = analyze_contract(contract)
        if error:
            messages.error(self.request, error)
        else:
            messages.success(self.request, _("KI-Analyse abgeschlossen."))
        return response

    def get_success_url(self):
        return reverse('contracts:contract_detail', args=[self.object.id])


class ContractUpdateView(ContractsEditMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        contract = self.object
        _data, error = analyze_contract(contract)
        if error:
            messages.error(self.request, error)
        else:
            messages.success(self.request, _("KI-Analyse abgeschlossen."))
        return response

    def get_success_url(self):
        return reverse('contracts:contract_detail', args=[self.object.id])


class ContractVersionCreateView(ContractsEditMixin, CreateView):
    model = ContractVersion
    form_class = ContractVersionForm
    template_name = 'contracts/contract_version_form.html'

    def get_initial(self):
        initial = super().get_initial()
        contract_id = self.kwargs.get('contract_id')
        if contract_id:
            initial['contract'] = contract_id
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        contract = self.object.contract
        _data, error = analyze_contract(contract)
        if error:
            messages.error(self.request, error)
        else:
            messages.success(self.request, _("KI-Analyse abgeschlossen."))
        return response

    def get_success_url(self):
        return reverse('contracts:contract_detail', args=[self.object.contract.id])


class ContractAnalyzeView(ContractsEditMixin, TemplateView):
    template_name = 'contracts/contract_detail.html'

    def post(self, request, *args, **kwargs):
        contract_id = kwargs.get('pk')
        contract = Contract.objects.get(pk=contract_id)
        _data, error = analyze_contract(contract)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, _("KI-Analyse abgeschlossen."))
        return redirect('contracts:contract_detail', pk=contract_id)


class ContractExportAnalysisView(ContractsEditMixin, TemplateView):
    template_name = 'contracts/contract_detail.html'

    def post(self, request, *args, **kwargs):
        contract_id = kwargs.get('pk')
        contract = Contract.objects.get(pk=contract_id)
        return export_contract_analysis_docx(contract)


class ContractsHelpView(ContractsViewMixin, TemplateView):
    template_name = 'contracts/help.html'
