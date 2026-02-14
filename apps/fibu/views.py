import csv
from io import StringIO
from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.db import models
from .models import Account, CostCenter, CostType, BusinessPartner, JournalEntry, JournalLine
from .forms import (
    AccountForm,
    CostCenterForm,
    CostTypeForm,
    BusinessPartnerForm,
    JournalEntryForm,
    JournalLineForm,
    FibuSettingsForm,
    AccountImportForm,
)
from .models import FibuSettings


class FibuBaseView(LoginRequiredMixin):
    login_url = '/cloudstorage/accounts/login/'


class AccountListView(FibuBaseView, ListView):
    model = Account
    template_name = 'fibu/account_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        qs = Account.objects.all().order_by('code')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(models.Q(code__icontains=q) | models.Q(name__icontains=q))
        return qs


class AccountCreateView(FibuBaseView, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'fibu/form.html'
    success_url = '/fibu/accounts/'


class AccountImportView(FibuBaseView, TemplateView):
    template_name = 'fibu/account_import.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['form'] = AccountImportForm()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = AccountImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, _("Bitte eine CSV-Datei auswählen."))
            return redirect('/fibu/accounts/import/')

        upload = form.cleaned_data['file']
        raw = upload.read().decode('utf-8', errors='ignore')
        if not raw.strip():
            messages.error(request, _("Die Datei ist leer."))
            return redirect('/fibu/accounts/import/')

        first_line = raw.splitlines()[0] if raw.splitlines() else ''
        delimiter = ';' if ';' in first_line else ','
        reader = csv.DictReader(StringIO(raw), delimiter=delimiter)

        created = 0
        updated = 0
        skipped = 0
        allowed_types = {key for key, _ in Account.TYPES}

        for row in reader:
            code = (row.get('code') or row.get('konto') or '').strip()
            name = (row.get('name') or row.get('bezeichnung') or '').strip()
            if not code or not name:
                skipped += 1
                continue
            account_type = (row.get('account_type') or row.get('typ') or 'expense').strip().lower()
            if account_type not in allowed_types:
                account_type = 'expense'

            obj, created_flag = Account.objects.update_or_create(
                code=code,
                defaults={'name': name, 'account_type': account_type, 'is_active': True},
            )
            if created_flag:
                created += 1
            else:
                updated += 1

        messages.success(
            request,
            _("Import abgeschlossen: %(created)s neu, %(updated)s aktualisiert, %(skipped)s übersprungen.") % {"created": created, "updated": updated, "skipped": skipped},
        )
        return redirect('/fibu/accounts/')


class CostCenterListView(FibuBaseView, ListView):
    model = CostCenter
    template_name = 'fibu/costcenter_list.html'
    context_object_name = 'centers'

    def get_queryset(self):
        qs = CostCenter.objects.all().order_by('code')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(models.Q(code__icontains=q) | models.Q(name__icontains=q))
        return qs


class CostCenterCreateView(FibuBaseView, CreateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'fibu/form.html'
    success_url = '/fibu/cost-centers/'


class CostTypeListView(FibuBaseView, ListView):
    model = CostType
    template_name = 'fibu/costtype_list.html'
    context_object_name = 'types'

    def get_queryset(self):
        qs = CostType.objects.all().order_by('code')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(models.Q(code__icontains=q) | models.Q(name__icontains=q))
        return qs


class CostTypeCreateView(FibuBaseView, CreateView):
    model = CostType
    form_class = CostTypeForm
    template_name = 'fibu/form.html'
    success_url = '/fibu/cost-types/'


class BusinessPartnerListView(FibuBaseView, ListView):
    model = BusinessPartner
    template_name = 'fibu/partner_list.html'
    context_object_name = 'partners'

    def get_queryset(self):
        qs = BusinessPartner.objects.all().order_by('name')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                models.Q(name__icontains=q)
                | models.Q(partner_number__icontains=q)
                | models.Q(vat_id__icontains=q)
            )
        return qs


class BusinessPartnerCreateView(FibuBaseView, CreateView):
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'fibu/form.html'
    success_url = '/fibu/partners/'


class JournalEntryListView(FibuBaseView, ListView):
    model = JournalEntry
    template_name = 'fibu/journal_list.html'
    context_object_name = 'entries'

    def get_queryset(self):
        qs = JournalEntry.objects.all().order_by('-date', '-id')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(models.Q(reference__icontains=q) | models.Q(description__icontains=q))
        return qs


class JournalEntryCreateView(FibuBaseView, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'fibu/form.html'
    success_url = '/fibu/journal/'


class JournalEntryDetailView(FibuBaseView, DetailView):
    model = JournalEntry
    template_name = 'fibu/journal_detail.html'
    context_object_name = 'entry'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = JournalLine.objects.filter(entry=self.object).select_related(
            'account', 'cost_center', 'cost_type', 'partner'
        )
        context['line_form'] = JournalLineForm()
        return context


class FibuHelpView(FibuBaseView, TemplateView):
    template_name = 'fibu/help.html'


class FibuSettingsView(FibuBaseView, TemplateView):
    template_name = 'fibu/settings.html'

    def get(self, request, *args, **kwargs):
        settings_obj = FibuSettings.get_settings()
        form = FibuSettingsForm(instance=settings_obj)
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        settings_obj = FibuSettings.get_settings()
        form = FibuSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _("FiBu-Einstellungen gespeichert."))
        else:
            messages.error(request, _("Bitte prüfe die FiBu-Einstellungen."))
        return redirect('/fibu/settings/')
