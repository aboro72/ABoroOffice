from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import (
    Account,
    Lead,
    Opportunity,
    Activity,
    Note,
    EmailTemplate,
    EmailLog,
    LeadSourceProfile,
    LeadStaging,
)
from .forms import (
    AccountForm,
    LeadForm,
    OpportunityForm,
    EmailTemplateForm,
    EmailSendForm,
    LeadSourceProfileForm,
    LeadStagingForm,
    NoteForm,
    ActivityForm,
)
from .permissions import CrmViewMixin, CrmEditMixin, can_edit_crm, can_view_crm
from .services.ai import CrmAIService
from .services.scoring import update_lead_score
from .services.lead_sources import run_import_for_profile
from .services.enrichment import enrich_lead_from_website
from .services.enrichment import enrich_queryset


def _normalize_staging_address(item: LeadStaging) -> str:
    raw = item.raw_data if isinstance(item.raw_data, dict) else {}
    if raw.get('address'):
        return raw.get('address')
    street = raw.get('strasse') or raw.get('street') or ''
    zip_code = raw.get('postleitzahl') or raw.get('zip') or ''
    city = raw.get('ort') or raw.get('city') or ''
    country = raw.get('land') or raw.get('country') or ''
    parts = [p for p in [street, " ".join([zip_code, city]).strip(), country] if p]
    address = ", ".join(parts)
    if address:
        raw['address'] = address
        item.raw_data = raw
        item.save(update_fields=['raw_data'])
    return address


def _get_staging_website(item: LeadStaging) -> str:
    raw = item.raw_data if isinstance(item.raw_data, dict) else {}
    return raw.get('website') or raw.get('source_url') or ''


class CrmHomeView(CrmViewMixin, TemplateView):
    template_name = 'crm/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accounts_count'] = Account.objects.count()
        context['leads_count'] = Lead.objects.count()
        context['opps_count'] = Opportunity.objects.count()
        context['open_activities'] = Activity.objects.filter(status='open').count()
        context['can_edit'] = can_edit_crm(self.request.user)
        return context


class AccountListView(CrmViewMixin, ListView):
    model = Account
    template_name = 'crm/account_list.html'
    context_object_name = 'accounts'
    paginate_by = 25

    def get_queryset(self):
        qs = Account.objects.all()
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        sort = self.request.GET.get('sort', '-updated_at').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        if status:
            qs = qs.filter(status=status)
        allowed_sorts = {'name', '-name', 'updated_at', '-updated_at'}
        if sort not in allowed_sorts:
            sort = '-updated_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = can_edit_crm(self.request.user)
        context['list_sort_options'] = [
            ('-updated_at', 'Neueste zuerst'),
            ('updated_at', 'Älteste zuerst'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
        ]
        context['current_sort'] = self.request.GET.get('sort', '-updated_at')
        return context


class AccountDetailView(CrmViewMixin, DetailView):
    model = Account
    template_name = 'crm/account_detail.html'
    context_object_name = 'account'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action')
        if action == 'ai_summary':
            try:
                ai = CrmAIService()
                summary = ai.summarize_account(self.object, recent_notes=self.object.notes.all()[:3])
                request.session['crm_ai_summary'] = summary
            except Exception as exc:
                messages.error(request, f'AI Fehler: {exc}')
        elif action == 'add_note':
            if not can_edit_crm(request.user):
                messages.error(request, "Keine Berechtigung.")
                return redirect(reverse('crm:account_detail', args=[self.object.pk]))
            form = NoteForm(request.POST)
            if form.is_valid():
                note = form.save(commit=False)
                note.account = self.object
                note.created_by = request.user
                note.save()
                messages.success(request, "Notiz gespeichert.")
            else:
                messages.error(request, "Notiz ist ungültig.")
        elif action == 'add_activity':
            if not can_edit_crm(request.user):
                messages.error(request, "Keine Berechtigung.")
                return redirect(reverse('crm:account_detail', args=[self.object.pk]))
            form = ActivityForm(request.POST)
            if form.is_valid():
                activity = form.save(commit=False)
                activity.account = self.object
                activity.owner = request.user
                activity.save()
                messages.success(request, "Aktivität gespeichert.")
            else:
                messages.error(request, "Aktivität ist ungültig.")
        return redirect(reverse('crm:account_detail', args=[self.object.pk]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ai_summary'] = self.request.session.pop('crm_ai_summary', None)
        context['can_edit'] = can_edit_crm(self.request.user)
        context['note_form'] = NoteForm()
        context['activity_form'] = ActivityForm()
        context['notes'] = self.object.notes.all().order_by('-created_at')[:20]
        context['activities'] = self.object.activities.all().order_by('-created_at')[:20]
        return context


class LeadListView(CrmViewMixin, ListView):
    model = Lead
    template_name = 'crm/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 25

    def get_queryset(self):
        qs = Lead.objects.all()
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        sort = self.request.GET.get('sort', '-updated_at').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        if status:
            qs = qs.filter(status=status)
        allowed_sorts = {'name', '-name', 'updated_at', '-updated_at', 'score', '-score'}
        if sort not in allowed_sorts:
            sort = '-updated_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = can_edit_crm(self.request.user)
        context['list_sort_options'] = [
            ('-updated_at', 'Neueste zuerst'),
            ('updated_at', 'Älteste zuerst'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
            ('-score', 'Score hoch'),
            ('score', 'Score niedrig'),
        ]
        context['current_sort'] = self.request.GET.get('sort', '-updated_at')
        return context


class LeadDetailView(CrmViewMixin, DetailView):
    model = Lead
    template_name = 'crm/lead_detail.html'
    context_object_name = 'lead'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action')
        if action == 'ai_summary':
            try:
                ai = CrmAIService()
                self.object.ai_status = 'running'
                self.object.ai_error = ''
                self.object.save(update_fields=['ai_status', 'ai_error'])
                data = ai.summarize_lead_with_next_steps(self.object, recent_notes=self.object.notes.all()[:5])
                summary = data.get('summary', '')
                next_steps = data.get('next_steps', [])
                if isinstance(next_steps, list):
                    next_steps_text = "\n".join([str(item) for item in next_steps if item])
                else:
                    next_steps_text = str(next_steps or '')
                self.object.ai_summary = summary
                self.object.ai_next_steps = next_steps_text
                self.object.ai_last_analyzed = timezone.now()
                self.object.ai_status = 'done'
                self.object.save(update_fields=[
                    'ai_summary',
                    'ai_next_steps',
                    'ai_last_analyzed',
                    'ai_status',
                ])
            except Exception as exc:
                self.object.ai_status = 'error'
                self.object.ai_error = str(exc)
                self.object.save(update_fields=['ai_status', 'ai_error'])
                messages.error(request, f'AI Fehler: {exc}')
        elif action == 'ai_followup':
            try:
                ai = CrmAIService()
                self.object.ai_status = 'running'
                self.object.ai_error = ''
                self.object.save(update_fields=['ai_status', 'ai_error'])
                data = ai.draft_lead_followup_email(self.object, recent_notes=self.object.notes.all()[:5])
                self.object.ai_followup_subject = data.get('subject', '')
                self.object.ai_followup_body = data.get('body', '')
                self.object.ai_last_analyzed = timezone.now()
                self.object.ai_status = 'done'
                self.object.save(update_fields=[
                    'ai_followup_subject',
                    'ai_followup_body',
                    'ai_last_analyzed',
                    'ai_status',
                ])
            except Exception as exc:
                self.object.ai_status = 'error'
                self.object.ai_error = str(exc)
                self.object.save(update_fields=['ai_status', 'ai_error'])
                messages.error(request, f'AI Fehler: {exc}')
        elif action == 'ai_qa':
            question = request.POST.get('question', '').strip()
            if not question:
                messages.error(request, "Bitte eine Frage eingeben.")
                return redirect(reverse('crm:lead_detail', args=[self.object.pk]))
            try:
                ai = CrmAIService()
                self.object.ai_status = 'running'
                self.object.ai_error = ''
                self.object.save(update_fields=['ai_status', 'ai_error'])
                answer = ai.answer_lead_question(self.object, question, recent_notes=self.object.notes.all()[:5])
                self.object.ai_last_question = question
                self.object.ai_last_answer = answer
                self.object.ai_last_analyzed = timezone.now()
                self.object.ai_status = 'done'
                self.object.save(update_fields=[
                    'ai_last_question',
                    'ai_last_answer',
                    'ai_last_analyzed',
                    'ai_status',
                ])
            except Exception as exc:
                self.object.ai_status = 'error'
                self.object.ai_error = str(exc)
                self.object.save(update_fields=['ai_status', 'ai_error'])
                messages.error(request, f'AI Fehler: {exc}')
        elif action == 'enrich_lead':
            if not can_edit_crm(request.user):
                messages.error(request, "Keine Berechtigung.")
                return redirect(reverse('crm:lead_detail', args=[self.object.pk]))
            try:
                updated = enrich_lead_from_website(self.object)
                if updated:
                    messages.success(request, "Lead aus Website angereichert.")
                else:
                    messages.info(request, "Keine neuen Daten gefunden.")
            except Exception as exc:
                messages.error(request, f"Enrich Fehler: {exc}")
        elif action == 'add_note':
            if not can_edit_crm(request.user):
                messages.error(request, "Keine Berechtigung.")
                return redirect(reverse('crm:lead_detail', args=[self.object.pk]))
            form = NoteForm(request.POST)
            if form.is_valid():
                note = form.save(commit=False)
                note.lead = self.object
                note.created_by = request.user
                note.save()
                messages.success(request, "Notiz gespeichert.")
            else:
                messages.error(request, "Notiz ist ungültig.")
        elif action == 'add_activity':
            if not can_edit_crm(request.user):
                messages.error(request, "Keine Berechtigung.")
                return redirect(reverse('crm:lead_detail', args=[self.object.pk]))
            form = ActivityForm(request.POST)
            if form.is_valid():
                activity = form.save(commit=False)
                activity.lead = self.object
                activity.owner = request.user
                activity.save()
                messages.success(request, "Aktivität gespeichert.")
            else:
                messages.error(request, "Aktivität ist ungültig.")
        elif action == 'recalc_score':
            if can_edit_crm(request.user):
                update_lead_score(self.object, use_ai=True)
                messages.success(request, "Lead-Score wurde aktualisiert.")
            else:
                messages.error(request, "Keine Berechtigung.")
        elif action == 'send_email':
            if not can_edit_crm(request.user):
                messages.error(request, "Keine Berechtigung.")
                return redirect(reverse('crm:lead_detail', args=[self.object.pk]))
            form = EmailSendForm(request.POST)
            if form.is_valid():
                template_obj = form.cleaned_data['template']
                to_email = form.cleaned_data['to_email']
                context = {
                    'lead': self.object,
                    'user': request.user,
                }
                subject = Template(template_obj.subject).render(Context(context))
                body = Template(template_obj.body).render(Context(context))
                try:
                    send_mail(subject, body, settings.EMAIL_HOST_USER, [to_email], fail_silently=False)
                    EmailLog.objects.create(
                        template=template_obj,
                        to_email=to_email,
                        subject=subject,
                        body=body,
                        lead=self.object,
                        created_by=request.user,
                        status='sent',
                    )
                    messages.success(request, "E-Mail gesendet.")
                except Exception as exc:
                    EmailLog.objects.create(
                        template=template_obj,
                        to_email=to_email,
                        subject=subject,
                        body=body,
                        lead=self.object,
                        created_by=request.user,
                        status='failed',
                        error_message=str(exc),
                    )
                    messages.error(request, f"E-Mail Fehler: {exc}")
            else:
                messages.error(request, "E-Mail-Formular ist ungueltig.")
        return redirect(reverse('crm:lead_detail', args=[self.object.pk]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.ai_next_steps:
            context['ai_next_steps'] = [line for line in self.object.ai_next_steps.splitlines() if line.strip()]
        else:
            context['ai_next_steps'] = []
        context['can_edit'] = can_edit_crm(self.request.user)
        context['note_form'] = NoteForm()
        context['activity_form'] = ActivityForm()
        context['notes'] = self.object.notes.all().order_by('-created_at')[:20]
        context['activities'] = self.object.activities.all().order_by('-created_at')[:20]
        context['email_form'] = EmailSendForm(initial={'to_email': self.object.email})
        context['email_logs'] = self.object.email_logs.all().order_by('-sent_at')[:10]
        return context


class OpportunityListView(CrmViewMixin, ListView):
    model = Opportunity
    template_name = 'crm/opportunity_list.html'
    context_object_name = 'opportunities'
    paginate_by = 25

    def get_queryset(self):
        qs = Opportunity.objects.select_related('account').all()
        q = self.request.GET.get('q', '').strip()
        stage = self.request.GET.get('stage', '').strip()
        sort = self.request.GET.get('sort', '-updated_at').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        if stage:
            qs = qs.filter(stage=stage)
        allowed_sorts = {'name', '-name', 'updated_at', '-updated_at', 'amount', '-amount'}
        if sort not in allowed_sorts:
            sort = '-updated_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = can_edit_crm(self.request.user)
        context['opportunity_stage_choices'] = Opportunity.STAGE_CHOICES
        context['list_sort_options'] = [
            ('-updated_at', 'Neueste zuerst'),
            ('updated_at', 'Älteste zuerst'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
            ('-amount', 'Betrag hoch'),
            ('amount', 'Betrag niedrig'),
        ]
        context['current_sort'] = self.request.GET.get('sort', '-updated_at')
        return context


class OpportunityDetailView(CrmViewMixin, DetailView):
    model = Opportunity
    template_name = 'crm/opportunity_detail.html'
    context_object_name = 'opportunity'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action')
        if action == 'ai_email':
            try:
                ai = CrmAIService()
                draft = ai.draft_opportunity_email(self.object)
                request.session['crm_ai_email'] = draft
            except Exception as exc:
                messages.error(request, f'AI Fehler: {exc}')
        elif action == 'send_email':
            if not can_edit_crm(request.user):
                messages.error(request, "Keine Berechtigung.")
                return redirect(reverse('crm:opportunity_detail', args=[self.object.pk]))
            form = EmailSendForm(request.POST)
            if form.is_valid():
                template_obj = form.cleaned_data['template']
                to_email = form.cleaned_data['to_email']
                context = {
                    'opportunity': self.object,
                    'account': self.object.account,
                    'user': request.user,
                }
                subject = Template(template_obj.subject).render(Context(context))
                body = Template(template_obj.body).render(Context(context))
                try:
                    send_mail(subject, body, settings.EMAIL_HOST_USER, [to_email], fail_silently=False)
                    EmailLog.objects.create(
                        template=template_obj,
                        to_email=to_email,
                        subject=subject,
                        body=body,
                        opportunity=self.object,
                        created_by=request.user,
                        status='sent',
                    )
                    messages.success(request, "E-Mail gesendet.")
                except Exception as exc:
                    EmailLog.objects.create(
                        template=template_obj,
                        to_email=to_email,
                        subject=subject,
                        body=body,
                        opportunity=self.object,
                        created_by=request.user,
                        status='failed',
                        error_message=str(exc),
                    )
                    messages.error(request, f"E-Mail Fehler: {exc}")
        return redirect(reverse('crm:opportunity_detail', args=[self.object.pk]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ai_email'] = self.request.session.pop('crm_ai_email', None)
        context['can_edit'] = can_edit_crm(self.request.user)
        context['email_form'] = EmailSendForm(initial={'to_email': self.object.account.email})
        context['email_logs'] = self.object.email_logs.all().order_by('-sent_at')[:10]
        return context


class OpportunityBoardView(CrmViewMixin, TemplateView):
    template_name = 'crm/opportunity_board.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stages = Opportunity.STAGE_CHOICES
        board = []
        for stage_key, stage_label in stages:
            items = Opportunity.objects.filter(stage=stage_key).order_by('-updated_at')
            board.append({
                'key': stage_key,
                'label': stage_label,
                'items': items,
            })
        context['board'] = board
        context['can_edit'] = can_edit_crm(self.request.user)
        return context


class AccountCreateView(CrmEditMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Account erstellen'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Account erstellt.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('crm:account_detail', args=[self.object.pk])


class AccountUpdateView(CrmEditMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Account bearbeiten'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Account aktualisiert.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('crm:account_detail', args=[self.object.pk])


class LeadCreateView(CrmEditMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Lead erstellen'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        update_lead_score(self.object, use_ai=True)
        try:
            if (not self.object.address or not self.object.phone) and self.object.website:
                enrich_lead_from_website(self.object)
        except Exception:
            pass
        messages.success(self.request, "Lead erstellt.")
        return response

    def get_success_url(self):
        return reverse('crm:lead_detail', args=[self.object.pk])


class LeadUpdateView(CrmEditMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Lead bearbeiten'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        update_lead_score(self.object, use_ai=True)
        try:
            if (not self.object.address or not self.object.phone) and self.object.website:
                enrich_lead_from_website(self.object)
        except Exception:
            pass
        messages.success(self.request, "Lead aktualisiert.")
        return response

    def get_success_url(self):
        return reverse('crm:lead_detail', args=[self.object.pk])


class OpportunityCreateView(CrmEditMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Opportunity erstellen'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Opportunity erstellt.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('crm:opportunity_detail', args=[self.object.pk])


class OpportunityUpdateView(CrmEditMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Opportunity bearbeiten'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Opportunity aktualisiert.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('crm:opportunity_detail', args=[self.object.pk])


class EmailTemplateListView(CrmEditMixin, ListView):
    model = EmailTemplate
    template_name = 'crm/email_templates.html'
    context_object_name = 'templates'
    paginate_by = 25

    def get_queryset(self):
        return EmailTemplate.objects.all().order_by('-updated_at')


class EmailTemplateCreateView(CrmEditMixin, CreateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'E-Mail Template erstellen'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "E-Mail-Template erstellt.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('crm:email_template_list')


class EmailTemplateUpdateView(CrmEditMixin, UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'E-Mail Template bearbeiten'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def form_valid(self, form):
        messages.success(self.request, "E-Mail-Template aktualisiert.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('crm:email_template_list')


class LeadSourceProfileListView(CrmEditMixin, ListView):
    model = LeadSourceProfile
    template_name = 'crm/lead_sources_list.html'
    context_object_name = 'profiles'
    paginate_by = 25

    def get_queryset(self):
        return LeadSourceProfile.objects.all().order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context


class LeadSourceProfileCreateView(CrmEditMixin, CreateView):
    model = LeadSourceProfile
    form_class = LeadSourceProfileForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Lead-Quelle erstellen'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def get_success_url(self):
        return reverse('crm:lead_sources')


class LeadSourceProfileUpdateView(CrmEditMixin, UpdateView):
    model = LeadSourceProfile
    form_class = LeadSourceProfileForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Lead-Quelle bearbeiten'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def get_success_url(self):
        return reverse('crm:lead_sources')


class LeadSourceRunView(CrmEditMixin, TemplateView):
    template_name = 'crm/lead_source_run.html'

    def post(self, request, *args, **kwargs):
        profile_id = kwargs.get('pk')
        profile = LeadSourceProfile.objects.get(pk=profile_id)
        run_import_for_profile(profile)
        messages.success(request, "Import gestartet.")
        return redirect('crm:lead_sources')


class LeadStagingListView(CrmEditMixin, ListView):
    model = LeadStaging
    template_name = 'crm/lead_staging_list.html'
    context_object_name = 'items'
    paginate_by = 50

    def get_queryset(self):
        qs = LeadStaging.objects.select_related('profile').all().order_by('-created_at')
        status = self.request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)
        no_website = self.request.GET.get('no_website', '').strip()
        if no_website:
            items = [item for item in qs if not _get_staging_website(item)]
            return items
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = context.get('items', [])
        for item in items:
            website = _get_staging_website(item)
            label = website.replace('https://', '').replace('http://', '').replace('www.', '')
            item.website_display_url = website
            item.website_display_label = label or website
            item.address_display = _normalize_staging_address(item) or ""
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        context['selected_no_website'] = self.request.GET.get('no_website', '').strip()
        return context


class LeadStagingNeedsWebsiteView(CrmEditMixin, ListView):
    model = LeadStaging
    template_name = 'crm/lead_staging_needs_website.html'
    context_object_name = 'items'
    paginate_by = 100

    def get_queryset(self):
        qs = LeadStaging.objects.select_related('profile').all().order_by('-created_at')
        qs = qs.filter(status='needs_website')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = True
        return context


class LeadStagingBatchWebsiteUpdateView(CrmEditMixin, TemplateView):
    template_name = 'crm/lead_staging_import.html'

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids')
        updated = 0
        for item_id in ids:
            website = (request.POST.get(f'website_{item_id}') or '').strip()
            address = (request.POST.get(f'address_{item_id}') or '').strip()
            if not (website or address):
                continue
            item = LeadStaging.objects.get(pk=item_id)
            raw = item.raw_data if isinstance(item.raw_data, dict) else {}
            if website:
                raw['website'] = website
            if address:
                raw['address'] = address
            item.raw_data = raw
            if website and item.status == 'needs_website':
                item.status = 'incomplete'
            item.save(update_fields=['raw_data', 'status'])
            updated += 1
        messages.success(request, f"Websites/Adressen gespeichert: {updated}.")
        return redirect('crm:lead_staging_needs_website')


class LeadStagingUpdateView(CrmEditMixin, UpdateView):
    model = LeadStaging
    form_class = LeadStagingForm
    template_name = 'crm/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Staging-Lead bearbeiten'
        context['can_edit'] = True
        context['selected_status'] = self.request.GET.get('status', '').strip()
        return context

    def get_success_url(self):
        return reverse('crm:lead_staging')


class LeadStagingImportView(CrmEditMixin, TemplateView):
    template_name = 'crm/lead_staging_import.html'

    def post(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        item = LeadStaging.objects.get(pk=item_id)
        if not (item.name and item.company and item.email and item.phone and item.lead_source and item.lead_status):
            messages.error(request, "Pflichtfelder fehlen (Name, Firma, E-Mail, Telefon, Quelle, Status).")
            return redirect('crm:lead_staging')
        Lead.objects.create(
            name=item.name,
            company=item.company,
            email=item.email,
            phone=item.phone,
            website=_get_staging_website(item),
            address=_normalize_staging_address(item),
            source=item.lead_source,
            status=item.lead_status,
            owner=request.user,
        )
        item.status = 'imported'
        item.save(update_fields=['status'])
        messages.success(request, "Lead importiert.")
        return redirect('crm:lead_staging')


class LeadStagingBulkImportView(CrmEditMixin, TemplateView):
    template_name = 'crm/lead_staging_import.html'

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('selected_ids')
        action = request.POST.get('action', 'import')
        if not ids:
            messages.error(request, "Keine Einträge ausgewählt.")
            return redirect('crm:lead_staging')

        if action == 'enrich':
            items = list(LeadStaging.objects.filter(id__in=ids))
            with_site = [item for item in items if _get_staging_website(item)]
            without_site = [item for item in items if not _get_staging_website(item)]
            count = enrich_queryset(with_site)
            if without_site:
                LeadStaging.objects.filter(id__in=[i.id for i in without_site]).update(status='needs_website')
            messages.success(request, f"Auto-Enrichment abgeschlossen. Bearbeitet: {count}.")
            return redirect('crm:lead_staging')

        if action == 'mark_needs_website':
            LeadStaging.objects.filter(id__in=ids).update(status='needs_website')
            messages.success(request, "Status auf 'Website gesucht' gesetzt.")
            return redirect('crm:lead_staging')

        imported = 0
        skipped = 0
        for item in LeadStaging.objects.filter(id__in=ids):
            if item.status == 'imported':
                skipped += 1
                continue
            if not (item.name and item.company and item.email and item.phone and item.lead_source and item.lead_status):
                item.status = 'skipped'
                item.save(update_fields=['status'])
                skipped += 1
                continue
            if Lead.objects.filter(email__iexact=item.email).exists():
                item.status = 'skipped'
                item.save(update_fields=['status'])
                skipped += 1
                continue
            if Lead.objects.filter(company__iexact=item.company, phone=item.phone).exists():
                item.status = 'skipped'
                item.save(update_fields=['status'])
                skipped += 1
                continue
            Lead.objects.create(
                name=item.name,
                company=item.company,
                email=item.email,
                phone=item.phone,
                website=_get_staging_website(item),
                address=_normalize_staging_address(item),
                source=item.lead_source,
                status=item.lead_status,
                owner=request.user,
            )
            item.status = 'imported'
            item.save(update_fields=['status'])
            imported += 1

        messages.success(request, f"Bulk-Import abgeschlossen. Importiert: {imported}, Übersprungen: {skipped}.")
        return redirect('crm:lead_staging')


class LeadStagingQuickUpdateView(CrmEditMixin, TemplateView):
    template_name = 'crm/lead_staging_import.html'

    def post(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        item = LeadStaging.objects.get(pk=item_id)
        website = (request.POST.get('website') or '').strip()
        address = (request.POST.get('address') or '').strip()
        raw = item.raw_data if isinstance(item.raw_data, dict) else {}
        if website:
            raw['website'] = website
        if address:
            raw['address'] = address
        item.raw_data = raw
        if website and item.status == 'needs_website':
            item.status = 'incomplete'
        item.save(update_fields=['raw_data', 'status'])
        messages.success(request, "Website/Adresse gespeichert.")
        return redirect('crm:lead_staging')


class CrmHelpView(CrmViewMixin, TemplateView):
    template_name = 'crm/help.html'


def _serialize_lead(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "name": lead.name,
        "company": lead.company,
        "email": lead.email,
        "phone": lead.phone,
        "website": lead.website,
        "address": lead.address,
        "source": lead.source,
        "status": lead.status,
        "score": lead.score,
        "rule_score": lead.rule_score,
        "ai_score": lead.ai_score,
        "score_reason": lead.score_reason,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


def _serialize_account(account: Account) -> dict:
    return {
        "id": account.id,
        "name": account.name,
        "industry": account.industry,
        "website": account.website,
        "phone": account.phone,
        "email": account.email,
        "address": account.address,
        "status": account.status,
        "owner_id": account.owner_id,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        "created_at": account.created_at.isoformat() if account.created_at else None,
    }


def _serialize_opportunity(opportunity: Opportunity) -> dict:
    return {
        "id": opportunity.id,
        "name": opportunity.name,
        "stage": opportunity.stage,
        "amount": float(opportunity.amount) if opportunity.amount is not None else 0,
        "close_date": opportunity.close_date.isoformat() if opportunity.close_date else None,
        "account_id": opportunity.account_id,
        "owner_id": opportunity.owner_id,
        "updated_at": opportunity.updated_at.isoformat() if opportunity.updated_at else None,
        "created_at": opportunity.created_at.isoformat() if opportunity.created_at else None,
    }


def _paginate(qs, request):
    try:
        limit = int(request.GET.get("limit", 50))
    except ValueError:
        limit = 50
    try:
        offset = int(request.GET.get("offset", 0))
    except ValueError:
        offset = 0
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    total = qs.count()
    items = qs[offset:offset + limit]
    return total, limit, offset, items


@login_required
@user_passes_test(can_view_crm)
def api_leads(request):
    qs = Lead.objects.all().order_by('-updated_at')
    status = request.GET.get("status", "").strip()
    q = request.GET.get("q", "").strip()
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(name__icontains=q)
    total, limit, offset, items = _paginate(qs, request)
    return JsonResponse({
        "count": total,
        "limit": limit,
        "offset": offset,
        "results": [_serialize_lead(item) for item in items],
    })


@login_required
@user_passes_test(can_view_crm)
def api_lead_detail(request, pk: int):
    lead = Lead.objects.filter(pk=pk).first()
    if not lead:
        return JsonResponse({"error": "Lead not found"}, status=404)
    return JsonResponse(_serialize_lead(lead))


@login_required
@user_passes_test(can_view_crm)
def api_accounts(request):
    qs = Account.objects.all().order_by('-updated_at')
    status = request.GET.get("status", "").strip()
    q = request.GET.get("q", "").strip()
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(name__icontains=q)
    total, limit, offset, items = _paginate(qs, request)
    return JsonResponse({
        "count": total,
        "limit": limit,
        "offset": offset,
        "results": [_serialize_account(item) for item in items],
    })


@login_required
@user_passes_test(can_view_crm)
def api_account_detail(request, pk: int):
    account = Account.objects.filter(pk=pk).first()
    if not account:
        return JsonResponse({"error": "Account not found"}, status=404)
    return JsonResponse(_serialize_account(account))


@login_required
@user_passes_test(can_view_crm)
def api_opportunities(request):
    qs = Opportunity.objects.select_related('account').all().order_by('-updated_at')
    stage = request.GET.get("stage", "").strip()
    q = request.GET.get("q", "").strip()
    if stage:
        qs = qs.filter(stage=stage)
    if q:
        qs = qs.filter(name__icontains=q)
    total, limit, offset, items = _paginate(qs, request)
    return JsonResponse({
        "count": total,
        "limit": limit,
        "offset": offset,
        "results": [_serialize_opportunity(item) for item in items],
    })


@login_required
@user_passes_test(can_view_crm)
def api_opportunity_detail(request, pk: int):
    opportunity = Opportunity.objects.filter(pk=pk).first()
    if not opportunity:
        return JsonResponse({"error": "Opportunity not found"}, status=404)
    return JsonResponse(_serialize_opportunity(opportunity))
