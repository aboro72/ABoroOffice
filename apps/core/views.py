"""
Views for the Core app
"""

from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from urllib.parse import urlencode
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import csv
from django.core.mail import send_mail
from pathlib import Path
from apps.core.forms import (
    ThemeSettingsForm,
    BrandingSettingsForm,
    AppTogglesForm,
    DashboardSettingsForm,
    CRMFallbackSettingsForm,
    CRMEnrichmentSettingsForm,
    DunningSettingsForm,
    InvoiceSettingsForm,
    EmailLogSettingsForm,
    SchedulerSettingsForm,
    BedrockSettingsForm,
    MarketingRolesForm,
    ErpRolesForm,
    ErpPricingForm,
    ErpCompetitorForm,
)
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings, EmailLog
from apps.crm.permissions import can_view_crm
from apps.erp.permissions import can_view_erp


def quick_search(request):
    q = (request.GET.get('q') or '').strip()
    scope = (request.GET.get('scope') or '').strip()
    if not q:
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))

    def _redirect(path):
        params = urlencode({'q': q})
        return HttpResponseRedirect(f"{path}?{params}")

    if scope == 'crm' and can_view_crm(request.user):
        return _redirect('/crm/leads/')
    if scope == 'erp' and can_view_erp(request.user):
        return _redirect('/erp/customers/')

    if can_view_crm(request.user):
        return _redirect('/crm/leads/')
    if can_view_erp(request.user):
        return _redirect('/erp/customers/')
    return redirect('/dashboard/')


class HomeView(TemplateView):
    """Home page view"""
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Home - ABoroOffice'
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """General dashboard after login."""
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.cloude.cloude_apps.plugins.models import Plugin
            from apps.cloude.cloude_apps.plugins.hooks import hook_registry, UI_DASHBOARD_WIDGET
            settings_obj = SystemSettings.get_settings()
            default_pos = getattr(settings_obj, 'plugin_dashboard_position', 'bottom') or 'bottom'
            context['plugins'] = Plugin.objects.all().order_by('-uploaded_at')
            context['has_plugins'] = Plugin.objects.exists()
            position_map = {}
            row_map = {}
            for plugin in context['plugins']:
                if plugin.module_name:
                    position_map[plugin.module_name] = plugin.dashboard_position
                    row_map[plugin.module_name] = plugin.dashboard_row
                else:
                    position_map[plugin.slug.replace('-', '_')] = plugin.dashboard_position
                    row_map[plugin.slug.replace('-', '_')] = plugin.dashboard_row
            widgets = []
            handlers = hook_registry.get_handlers(UI_DASHBOARD_WIDGET)
            for handler in handlers:
                try:
                    provider = handler()
                    widget_data = provider.render(self.request)
                    if widget_data:
                        widget_data['module'] = handler.__module__
                        # Resolve row from plugin mapping
                        row = 1
                        for mod, r in row_map.items():
                            if handler.__module__.startswith(mod):
                                row = r
                                break
                        widget_data['row'] = row
                        widgets.append(widget_data)
                except Exception:
                    continue
            widgets.sort(key=lambda w: w.get('order', 100))
            context['widgets'] = widgets
            # Split widgets by position
            buckets = {k: [] for k in ['top', 'bottom', 'left', 'right', 'center']}
            for widget in widgets:
                module = widget.get('module', '')
                pos = None
                for mod, p in position_map.items():
                    if module.startswith(mod):
                        pos = p
                        break
                if not pos or pos == 'inherit':
                    pos = default_pos
                buckets.get(pos, buckets['bottom']).append(widget)
            # sort each bucket by row then order
            for key in buckets:
                buckets[key].sort(key=lambda w: (w.get('row', 1), w.get('order', 100)))
            context['widgets_top'] = buckets['top']
            context['widgets_bottom'] = buckets['bottom']
            context['widgets_left'] = buckets['left']
            context['widgets_right'] = buckets['right']
            context['widgets_center'] = buckets['center']
        except Exception:
            context['plugins'] = []
            context['has_plugins'] = False
            context['widgets'] = []
            context['widgets_top'] = []
            context['widgets_bottom'] = []
            context['widgets_left'] = []
            context['widgets_right'] = []
            context['widgets_center'] = []
        return context


class PluginCardsView(LoginRequiredMixin, TemplateView):
    """Partial renderer for dashboard content (AJAX refresh)."""
    template_name = 'partials/dashboard_main.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.cloude.cloude_apps.plugins.models import Plugin
            from apps.cloude.cloude_apps.plugins.hooks import hook_registry, UI_DASHBOARD_WIDGET
            settings_obj = SystemSettings.get_settings()
            default_pos = getattr(settings_obj, 'plugin_dashboard_position', 'bottom') or 'bottom'
            context['plugins'] = Plugin.objects.all().order_by('-uploaded_at')
            context['has_plugins'] = Plugin.objects.exists()
            position_map = {}
            row_map = {}
            for plugin in context['plugins']:
                if plugin.module_name:
                    position_map[plugin.module_name] = plugin.dashboard_position
                    row_map[plugin.module_name] = plugin.dashboard_row
                else:
                    position_map[plugin.slug.replace('-', '_')] = plugin.dashboard_position
                    row_map[plugin.slug.replace('-', '_')] = plugin.dashboard_row
            widgets = []
            handlers = hook_registry.get_handlers(UI_DASHBOARD_WIDGET)
            for handler in handlers:
                try:
                    provider = handler()
                    widget_data = provider.render(self.request)
                    if widget_data:
                        widget_data['module'] = handler.__module__
                        row = 1
                        for mod, r in row_map.items():
                            if handler.__module__.startswith(mod):
                                row = r
                                break
                        widget_data['row'] = row
                        widgets.append(widget_data)
                except Exception:
                    continue
            widgets.sort(key=lambda w: w.get('order', 100))
            context['widgets'] = widgets
            buckets = {k: [] for k in ['top', 'bottom', 'left', 'right', 'center']}
            for widget in widgets:
                module = widget.get('module', '')
                pos = None
                for mod, p in position_map.items():
                    if module.startswith(mod):
                        pos = p
                        break
                if not pos or pos == 'inherit':
                    pos = default_pos
                buckets.get(pos, buckets['bottom']).append(widget)
            for key in buckets:
                buckets[key].sort(key=lambda w: (w.get('row', 1), w.get('order', 100)))
            context['widgets_top'] = buckets['top']
            context['widgets_bottom'] = buckets['bottom']
            context['widgets_left'] = buckets['left']
            context['widgets_right'] = buckets['right']
            context['widgets_center'] = buckets['center']
        except Exception:
            context['plugins'] = []
            context['has_plugins'] = False
            context['widgets'] = []
            context['widgets_top'] = []
            context['widgets_bottom'] = []
            context['widgets_left'] = []
            context['widgets_right'] = []
            context['widgets_center'] = []
        return context


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Standalone admin dashboard (not Django admin)."""
    template_name = 'admin_dashboard.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        settings_obj = SystemSettings.get_settings()
        context['theme_form'] = ThemeSettingsForm(instance=settings_obj)
        context['branding_form'] = BrandingSettingsForm(instance=settings_obj)
        context['app_toggles_form'] = AppTogglesForm(system_settings=settings_obj)
        context['dashboard_form'] = DashboardSettingsForm(instance=settings_obj)
        context['crm_fallback_form'] = CRMFallbackSettingsForm(instance=settings_obj)
        context['crm_enrichment_form'] = CRMEnrichmentSettingsForm(instance=settings_obj)
        context['dunning_form'] = DunningSettingsForm(instance=settings_obj)
        context['invoice_form'] = InvoiceSettingsForm(instance=settings_obj)
        context['email_log_settings_form'] = EmailLogSettingsForm(instance=settings_obj)
        context['scheduler_form'] = SchedulerSettingsForm(instance=settings_obj)
        context['bedrock_form'] = BedrockSettingsForm(instance=settings_obj)
        context['marketing_roles_form'] = MarketingRolesForm(instance=settings_obj)
        context['erp_roles_form'] = ErpRolesForm(instance=settings_obj)
        context['erp_pricing_form'] = ErpPricingForm(instance=settings_obj)
        context['erp_competitor_form'] = ErpCompetitorForm(instance=settings_obj)
        context['email_preview'] = self.request.session.pop('email_preview', None)
        email_logs = EmailLog.objects.filter(archived=False)
        email_to = (self.request.GET.get('email_to') or '').strip()
        email_subject = (self.request.GET.get('email_subject') or '').strip()
        start_date = (self.request.GET.get('email_start') or '').strip()
        end_date = (self.request.GET.get('email_end') or '').strip()
        sort = (self.request.GET.get('email_sort') or '-created_at').strip()
        if email_to:
            email_logs = email_logs.filter(to_emails__icontains=email_to)
        if email_subject:
            email_logs = email_logs.filter(subject__icontains=email_subject)
        email_body = (self.request.GET.get('email_body') or '').strip()
        if email_body:
            email_logs = email_logs.filter(body__icontains=email_body)
        if start_date:
            email_logs = email_logs.filter(created_at__date__gte=start_date)
        if end_date:
            email_logs = email_logs.filter(created_at__date__lte=end_date)
        allowed_sorts = {
            'created_at', '-created_at',
            'subject', '-subject',
            'to_emails', '-to_emails',
        }
        if sort not in allowed_sorts:
            sort = '-created_at'
        email_logs = email_logs.order_by(sort)
        paginator = Paginator(email_logs, 20)
        page_number = self.request.GET.get('email_page') or 1
        page_obj = paginator.get_page(page_number)
        context['email_logs'] = page_obj
        context['email_filter'] = {
            'email_to': email_to,
            'email_subject': email_subject,
            'email_body': email_body,
            'email_start': start_date,
            'email_end': end_date,
            'email_sort': sort,
        }
        context['email_page'] = page_obj
        archived_qs = EmailLog.objects.filter(archived=True).order_by('-created_at')
        context['email_archived_logs'] = archived_qs[:50]
        context['email_archived_stats'] = {
            'count': archived_qs.count(),
            'oldest': archived_qs.last().created_at if archived_qs.exists() else None,
            'newest': archived_qs.first().created_at if archived_qs.exists() else None,
        }

        # Plugin data
        try:
            from apps.cloude.cloude_apps.plugins.models import Plugin, PluginLog
            context['plugins'] = Plugin.objects.all().order_by('-uploaded_at')
            context['plugin_logs'] = PluginLog.objects.all().order_by('-created_at')[:20]
            context['has_plugins'] = Plugin.objects.exists()
        except Exception:
            context['plugins'] = []
            context['plugin_logs'] = []
            context['has_plugins'] = False

        return context

    def get(self, request, *args, **kwargs):
        if request.GET.get('email_log_export') in ('1', 'pdf', 'xlsx'):
            qs = EmailLog.objects.filter(archived=False)
            if request.GET.get('email_log_export_archived') == '1':
                qs = EmailLog.objects.filter(archived=True)
            email_to = (request.GET.get('email_to') or '').strip()
            email_subject = (request.GET.get('email_subject') or '').strip()
            start_date = (request.GET.get('email_start') or '').strip()
            end_date = (request.GET.get('email_end') or '').strip()
            email_body = (request.GET.get('email_body') or '').strip()
            sort = (request.GET.get('email_sort') or '-created_at').strip()
            if email_to:
                qs = qs.filter(to_emails__icontains=email_to)
            if email_subject:
                qs = qs.filter(subject__icontains=email_subject)
            if email_body:
                qs = qs.filter(body__icontains=email_body)
            if start_date:
                qs = qs.filter(created_at__date__gte=start_date)
            if end_date:
                qs = qs.filter(created_at__date__lte=end_date)
            allowed_sorts = {
                'created_at', '-created_at',
                'subject', '-subject',
                'to_emails', '-to_emails',
            }
            if sort not in allowed_sorts:
                sort = '-created_at'
            qs = qs.order_by(sort)

            if request.GET.get('email_log_export') == 'pdf':
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                width, height = A4
                y = height - 40
                c.setFont('Helvetica-Bold', 12)
                c.drawString(40, y, 'E-Mail Log Export')
                y -= 20
                c.setFont('Helvetica', 9)
                for row in qs.iterator():
                    line = f"{row.created_at:%Y-%m-%d %H:%M} | {row.subject} | {row.to_emails}"
                    c.drawString(40, y, line[:120])
                    y -= 12
                    if y < 40:
                        c.showPage()
                        y = height - 40
                        c.setFont('Helvetica', 9)
                c.save()
                pdf = buffer.getvalue()
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename=email_log.pdf'
                return response

            if request.GET.get('email_log_export') == 'xlsx':
                try:
                    import openpyxl
                except Exception:
                    response = HttpResponse(content_type='text/plain')
                    response.write('openpyxl not installed')
                    return response
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = 'Email Log'
                ws.append(['created_at', 'subject', 'from_email', 'to_emails', 'body', 'source'])
                for row in qs.iterator():
                    ws.append([row.created_at, row.subject, row.from_email, row.to_emails, row.body, row.source])
                output = BytesIO()
                wb.save(output)
                output.seek(0)
                response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=email_log.xlsx'
                return response

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=email_log.csv'
            writer = csv.writer(response)
            writer.writerow(['created_at', 'subject', 'from_email', 'to_emails', 'body', 'source'])
            for row in qs.iterator():
                writer.writerow([
                    row.created_at,
                    row.subject,
                    row.from_email,
                    row.to_emails,
                    row.body,
                    row.source,
                ])
            return response
        if request.GET.get('email_log_archive') == '1':
            qs = EmailLog.objects.all()
            email_to = (request.GET.get('email_to') or '').strip()
            email_subject = (request.GET.get('email_subject') or '').strip()
            start_date = (request.GET.get('email_start') or '').strip()
            end_date = (request.GET.get('email_end') or '').strip()
            email_body = (request.GET.get('email_body') or '').strip()
            if email_to:
                qs = qs.filter(to_emails__icontains=email_to)
            if email_subject:
                qs = qs.filter(subject__icontains=email_subject)
            if email_body:
                qs = qs.filter(body__icontains=email_body)
            if start_date:
                qs = qs.filter(created_at__date__gte=start_date)
            if end_date:
                qs = qs.filter(created_at__date__lte=end_date)
            qs.update(archived=True)
            messages.success(request, 'Gefilterte E-Mails wurden archiviert.')
            return redirect('admin_dashboard')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, 'Access denied')
            return redirect('admin_dashboard')

        settings_obj = SystemSettings.get_settings()

        # Theme settings update
        if 'save_theme' in request.POST:
            form = ThemeSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Theme-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Theme-Felder.')
            return redirect('admin_dashboard')

        # Branding settings update
        if 'save_branding' in request.POST:
            form = BrandingSettingsForm(request.POST, request.FILES, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Branding gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Branding-Felder.')
            return redirect('admin_dashboard')

        # App toggles update
        if 'save_app_toggles' in request.POST:
            form = AppTogglesForm(request.POST, system_settings=settings_obj)
            if form.is_valid():
                prev = settings_obj.app_toggles or {}
                new_toggles = {
                    'approvals': bool(form.cleaned_data.get('approvals')),
                    'helpdesk': bool(form.cleaned_data.get('helpdesk', True)),
                    'cloudstorage': bool(form.cleaned_data.get('cloudstorage', True)),
                    'classroom': bool(form.cleaned_data.get('classroom', True)),
                    'crm': bool(form.cleaned_data.get('crm', False)),
                    'contracts': bool(form.cleaned_data.get('contracts', False)),
                    'marketing': bool(form.cleaned_data.get('marketing', False)),
                    'erp': bool(form.cleaned_data.get('erp', False)),
                    'personnel': bool(form.cleaned_data.get('personnel', False)),
                    'fibu': bool(form.cleaned_data.get('fibu', False)),
                    'projects': bool(form.cleaned_data.get('projects', False)),
                    'workflows': bool(form.cleaned_data.get('workflows', False)),
                }
                settings_obj.app_toggles = new_toggles
                settings_obj.save()

                # Archive approvals if turned off
                if prev.get('approvals', False) and not new_toggles.get('approvals', False):
                    from apps.approvals.models import Approval
                    Approval.objects.update(archived=True)

                messages.success(request, 'App-Toggles gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die App-Toggles.')
            return redirect('admin_dashboard')

        if 'save_dashboard' in request.POST:
            form = DashboardSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Dashboard-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Dashboard-Einstellungen.')
            return redirect('admin_dashboard')
        if 'save_crm_fallback' in request.POST:
            form = CRMFallbackSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'CRM-Fallback-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die CRM-Fallback-Einstellungen.')
            return redirect('admin_dashboard')
        if 'save_crm_enrichment' in request.POST:
            form = CRMEnrichmentSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'CRM-Enrichment-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die CRM-Enrichment-Einstellungen.')
            return redirect('admin_dashboard')

        if 'save_dunning' in request.POST:
            form = DunningSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Mahnwesen-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Mahnwesen-Einstellungen.')
            return redirect('admin_dashboard')

        if 'save_invoice_settings' in request.POST:
            form = InvoiceSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Rechnungsversand-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Rechnungsversand-Einstellungen.')
            return redirect('admin_dashboard')

        if 'save_scheduler_settings' in request.POST:
            form = SchedulerSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Zeitplan-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Zeitplan-Einstellungen.')
            return redirect('admin_dashboard')

        if 'save_email_log_settings' in request.POST:
            form = EmailLogSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'E-Mail-Log Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die E-Mail-Log Einstellungen.')
            return redirect('admin_dashboard')

        if 'preview_email_templates' in request.POST:
            mapping = {
                'invoice_number': 'INV-2026-00001',
                'dunning_number': 'MN-2026-00001',
                'amount': '1.234,00 EUR',
                'due_date': '2026-02-28',
                'customer_name': 'Beispiel GmbH',
                'company_name': settings_obj.company_name or 'Unternehmen',
            }
            inv_subject_tpl = settings_obj.invoice_email_subject_template or f"Rechnung {mapping['invoice_number']}"
            inv_body_tpl = settings_obj.invoice_email_body_template or "Standardtext (Rechnung)"
            dun_subject_tpl = settings_obj.dunning_email_subject_template or f"Mahnung {mapping['dunning_number']}"
            dun_body_tpl = settings_obj.dunning_email_body_template or "Standardtext (Mahnung)"

            def _safe_fmt(template: str) -> str:
                try:
                    return template.format_map(mapping)
                except Exception:
                    return template

            request.session['email_preview'] = {
                'invoice_subject': _safe_fmt(inv_subject_tpl),
                'invoice_body': _safe_fmt(inv_body_tpl),
                'dunning_subject': _safe_fmt(dun_subject_tpl),
                'dunning_body': _safe_fmt(dun_body_tpl),
            }
            messages.success(request, 'E-Mail Vorschau aktualisiert.')
            return redirect('admin_dashboard')

        if 'send_test_email' in request.POST:
            to_email = (request.POST.get('test_email_to') or '').strip()
            email_type = (request.POST.get('test_email_type') or 'invoice').strip()
            if not to_email:
                messages.error(request, 'Bitte eine Ziel-E-Mail angeben.')
                return redirect('admin_dashboard')

            mapping = {
                'invoice_number': 'INV-2026-00001',
                'dunning_number': 'MN-2026-00001',
                'amount': '1.234,00 EUR',
                'due_date': '2026-02-28',
                'customer_name': 'Beispiel GmbH',
                'company_name': settings_obj.company_name or 'Unternehmen',
            }

            def _safe_fmt(template: str) -> str:
                try:
                    return template.format_map(mapping)
                except Exception:
                    return template

            if email_type == 'dunning':
                subject_tpl = settings_obj.dunning_email_subject_template or f"Mahnung {mapping['dunning_number']}"
                body_tpl = settings_obj.dunning_email_body_template or "Standardtext (Mahnung)"
            else:
                subject_tpl = settings_obj.invoice_email_subject_template or f"Rechnung {mapping['invoice_number']}"
                body_tpl = settings_obj.invoice_email_body_template or "Standardtext (Rechnung)"

            subject = _safe_fmt(subject_tpl)
            body = _safe_fmt(body_tpl)
            from_email = settings_obj.company_email or settings_obj.smtp_username or None
            send_mail(subject, body, from_email, [to_email], fail_silently=True)
            messages.success(request, f'Test-E-Mail gesendet an {to_email}.')
            return redirect('admin_dashboard')

        if 'restore_email_log' in request.POST:
            log_id = request.POST.get('restore_email_log')
            EmailLog.objects.filter(id=log_id).update(archived=False)
            messages.success(request, 'E-Mail wiederhergestellt.')
            return redirect('admin_dashboard')

        if 'restore_archived_filtered' in request.POST:
            qs = EmailLog.objects.filter(archived=True)
            email_to = (request.POST.get('email_to') or '').strip()
            email_subject = (request.POST.get('email_subject') or '').strip()
            email_body = (request.POST.get('email_body') or '').strip()
            start_date = (request.POST.get('email_start') or '').strip()
            end_date = (request.POST.get('email_end') or '').strip()
            if email_to:
                qs = qs.filter(to_emails__icontains=email_to)
            if email_subject:
                qs = qs.filter(subject__icontains=email_subject)
            if email_body:
                qs = qs.filter(body__icontains=email_body)
            if start_date:
                qs = qs.filter(created_at__date__gte=start_date)
            if end_date:
                qs = qs.filter(created_at__date__lte=end_date)
            qs.update(archived=False)
            messages.success(request, 'Archivierte E-Mails wurden wiederhergestellt.')
            return redirect('admin_dashboard')
        if 'restore_archived_all' in request.POST:
            EmailLog.objects.filter(archived=True).update(archived=False)
            messages.success(request, 'Archiv komplett wiederhergestellt.')
            return redirect('admin_dashboard')

        if 'save_marketing_roles' in request.POST:
            form = MarketingRolesForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Marketing-Rollen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Marketing-Rollen.')
            return redirect('admin_dashboard')

        if 'save_erp_roles' in request.POST:
            form = ErpRolesForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'ERP-Rollen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die ERP-Rollen.')
            return redirect('admin_dashboard')

        if 'save_erp_pricing' in request.POST:
            form = ErpPricingForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'ERP-Preislogik gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die ERP-Preislogik.')
            return redirect('admin_dashboard')

        if 'save_erp_competitor' in request.POST:
            form = ErpCompetitorForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'ERP Konkurrenz-Provider gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Konkurrenz-Provider Einstellungen.')
            return redirect('admin_dashboard')

        if 'save_bedrock' in request.POST:
            form = BedrockSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Bedrock-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Bedrock-Einstellungen.')
            return redirect('admin_dashboard')

        # Plugin upload
        zip_file = request.FILES.get('zip_file')
        if zip_file:
            try:
                from apps.cloude.cloude_apps.plugins.loader import PluginLoader
                from apps.cloude.cloude_apps.plugins.models import Plugin, PluginLog

                loader = PluginLoader()
                temp_path = Path('/tmp') / zip_file.name
                with open(temp_path, 'wb+') as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)

                manifest = loader.validate_zip(temp_path)
                plugin = Plugin.objects.create(
                    name=manifest['name'],
                    slug=manifest['slug'],
                    version=manifest['version'],
                    author=manifest.get('author', 'Unknown'),
                    description=manifest.get('description', ''),
                    zip_file=zip_file,
                    manifest=manifest,
                    installed_by=request.user,
                    status='inactive'
                )

                extract_dir = loader.extract_plugin(str(plugin.id), temp_path)
                plugin.extracted_path = str(extract_dir)
                plugin.save()

                PluginLog.objects.create(
                    plugin=plugin,
                    action='uploaded',
                    user=request.user,
                    message=f"Plugin uploaded by {request.user.username}"
                )

                messages.success(request, f'✅ Plugin "{plugin.name}" hochgeladen.')
            except Exception as e:
                messages.error(request, f'❌ Upload fehlgeschlagen: {str(e)}')

            return redirect('admin_dashboard')

        # Plugin dashboard position update
        if 'save_plugin_position' in request.POST:
            plugin_id = request.POST.get('plugin_id')
            dashboard_position = request.POST.get('dashboard_position', 'inherit')
            dashboard_row = request.POST.get('dashboard_row', '1')
            try:
                from apps.cloude.cloude_apps.plugins.models import Plugin
                plugin = Plugin.objects.get(pk=plugin_id)
                plugin.dashboard_position = dashboard_position
                try:
                    plugin.dashboard_row = int(dashboard_row)
                except Exception:
                    plugin.dashboard_row = 1
                plugin.save(update_fields=['dashboard_position', 'dashboard_row'])
                messages.success(request, 'Plugin-Position gespeichert.')
            except Exception:
                messages.error(request, 'Plugin-Position konnte nicht gespeichert werden.')
            return redirect('admin_dashboard')

        return redirect('admin_dashboard')


class SystemSettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Central system settings view."""
    template_name = 'system_settings.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings_obj = SystemSettings.get_settings()
        context['theme_form'] = ThemeSettingsForm(instance=settings_obj)
        context['branding_form'] = BrandingSettingsForm(instance=settings_obj)
        context['app_toggles_form'] = AppTogglesForm(system_settings=settings_obj)
        return context

    def post(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, 'Access denied')
            return redirect('system_settings')

        settings_obj = SystemSettings.get_settings()

        if 'save_theme' in request.POST:
            form = ThemeSettingsForm(request.POST, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Theme-Einstellungen gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Theme-Felder.')
            return redirect('system_settings')

        if 'save_branding' in request.POST:
            form = BrandingSettingsForm(request.POST, request.FILES, instance=settings_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Branding gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die Branding-Felder.')
            return redirect('system_settings')

        if 'save_app_toggles' in request.POST:
            form = AppTogglesForm(request.POST, system_settings=settings_obj)
            if form.is_valid():
                prev = settings_obj.app_toggles or {}
                new_toggles = {
                    'approvals': bool(form.cleaned_data.get('approvals')),
                    'helpdesk': bool(form.cleaned_data.get('helpdesk', True)),
                    'cloudstorage': bool(form.cleaned_data.get('cloudstorage', True)),
                    'classroom': bool(form.cleaned_data.get('classroom', True)),
                    'crm': bool(form.cleaned_data.get('crm', False)),
                    'contracts': bool(form.cleaned_data.get('contracts', False)),
                    'marketing': bool(form.cleaned_data.get('marketing', False)),
                    'erp': bool(form.cleaned_data.get('erp', False)),
                    'personnel': bool(form.cleaned_data.get('personnel', False)),
                    'fibu': bool(form.cleaned_data.get('fibu', False)),
                }
                settings_obj.app_toggles = new_toggles
                settings_obj.save()

                if prev.get('approvals', False) and not new_toggles.get('approvals', False):
                    from apps.approvals.models import Approval
                    Approval.objects.update(archived=True)

                messages.success(request, 'App-Toggles gespeichert.')
            else:
                messages.error(request, 'Bitte prüfe die App-Toggles.')
            return redirect('system_settings')

        return redirect('system_settings')


class ApiDocsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Unified API documentation landing page."""
    template_name = 'api_docs.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class BedrockTestView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'bedrock_test.html'


class UserGuideView(LoginRequiredMixin, TemplateView):
    template_name = 'user_guide.html'


class UserGuidePdfView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from pathlib import Path
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings

        resp = HttpResponse(content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="ABoroOffice_UserGuide.pdf"'
        c = canvas.Canvas(resp, pagesize=A4)
        width, height = A4
        y = height - 40
        path = Path('docs/USER_GUIDE.md')
        if path.exists():
            lines = path.read_text(encoding='utf-8').splitlines()
        else:
            lines = ["Dokumentation fehlt: docs/USER_GUIDE.md"]

        # Build TOC entries
        toc_entries = [line.lstrip("# ").strip() for line in lines if line.startswith("## ")]
        toc_line_height = 12
        toc_lines_per_page = int((height - 80) / toc_line_height)
        toc_pages = max(1, (len(toc_entries) + toc_lines_per_page - 1) // toc_lines_per_page)

        # Simulate content pagination to compute page numbers for headings
        content_page_start = 1 + toc_pages + 1  # cover + toc + content
        heading_pages = {}
        cur_page = content_page_start
        cur_y = height - 40
        for line in lines:
            if cur_y < 40:
                cur_page += 1
                cur_y = height - 40
            if line.startswith("#"):
                title = line.lstrip("# ").strip()
                if line.startswith("## "):
                    heading_pages[title] = cur_page
                cur_y -= 16
            else:
                cur_y -= 12

        settings_obj = SystemSettings.get_settings()
        version_label = settings_obj.company_version or "1.0"

        def _footer(page_no):
            c.setFont("Helvetica", 8)
            c.drawRightString(width - 40, 20, f"Seite {page_no}")
            c.setFont("Helvetica", 10)

        # Cover page
        # background band
        c.setFillColorRGB(0.1, 0.2, 0.35)
        c.rect(0, height - 180, width, 180, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(40, height - 80, "ABoroOffice")
        c.setFont("Helvetica", 12)
        c.drawString(40, height - 105, "Benutzerhandbuch")
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 11)
        c.drawString(40, height - 220, settings_obj.company_name or "ABoroOffice")
        c.setFont("Helvetica", 9)
        address = f"{settings_obj.company_address} · {settings_obj.company_postal_code} {settings_obj.company_city}"
        c.drawString(40, height - 235, address.strip())
        c.drawString(40, height - 248, settings_obj.company_email or "")
        c.setFont("Helvetica", 9)
        c.drawString(40, 50, f"Version: {version_label} · Datum: {timezone.now().date()}")
        # logo
        try:
            if settings_obj.logo and settings_obj.logo.path:
                c.drawImage(settings_obj.logo.path, width - 180, height - 120, width=120, height=50, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
        page_num = 1
        _footer(page_num)
        c.showPage()
        page_num += 1

        # TOC pages
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 40, "Inhaltsverzeichnis")
        c.setFont("Helvetica", 9)
        c.drawString(260, height - 40, "Seite")
        toc_y = height - 60
        for idx, entry in enumerate(toc_entries, start=1):
            if toc_y < 60:
                _footer(page_num)
                c.showPage()
                page_num += 1
                c.setFont("Helvetica-Bold", 14)
                c.drawString(40, height - 40, "Inhaltsverzeichnis")
                c.setFont("Helvetica", 9)
                c.drawString(260, height - 40, "Seite")
                toc_y = height - 60
            c.setFont("Helvetica", 9)
            c.drawString(40, toc_y, entry)
            c.drawString(260, toc_y, str(heading_pages.get(entry, content_page_start)))
            toc_y -= toc_line_height
        _footer(page_num)
        c.showPage()
        page_num += 1

        # Content pages
        y = height - 40
        c.setFont("Helvetica", 10)
        for line in lines:
            if y < 40:
                _footer(page_num)
                c.showPage()
                page_num += 1
                y = height - 40
                c.setFont("Helvetica", 10)
            if line.startswith("#"):
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y, line.lstrip("# ").strip())
                y -= 16
                c.setFont("Helvetica", 10)
                continue
            c.drawString(40, y, line[:120])
            y -= 12
        _footer(page_num)
        c.save()
        return resp


class UserGuideHtmlView(LoginRequiredMixin, TemplateView):
    template_name = 'user_guide_full.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        prompt = request.POST.get('prompt', '').strip()
        response_text = None
        error = None
        if not prompt:
            error = 'Bitte einen Prompt eingeben.'
        else:
            try:
                from django.conf import settings
                if not settings.BEDROCK_ENABLED:
                    error = 'Bedrock ist deaktiviert.'
                else:
                    from apps.core.services.bedrock import BedrockService
                    service = BedrockService()
                    response_text = service.converse(prompt)
            except Exception as exc:
                error = str(exc)

        context = self.get_context_data(**kwargs)
        context['prompt'] = prompt
        context['response_text'] = response_text
        context['error'] = error
        return self.render_to_response(context)


class HelpManualPdfView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from pathlib import Path
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings

        resp = HttpResponse(content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="ABoroOffice_Hilfehandbuch.pdf"'
        c = canvas.Canvas(resp, pagesize=A4)
        width, height = A4

        path = Path('docs/HELP_MANUAL_CLICK.md')
        lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else ['Dokumentation fehlt: docs/HELP_MANUAL.md']

        settings_obj = SystemSettings.get_settings()
        version_label = settings_obj.company_version or '1.0'

        def _footer(page_no):
            c.setFont('Helvetica', 8)
            c.drawRightString(width - 40, 20, f"Seite {page_no}")
            c.setFont('Helvetica', 10)

        # Build TOC entries
        toc_entries = [line.lstrip("# ").strip() for line in lines if line.startswith("## ")]
        toc_line_height = 12
        toc_lines_per_page = int((height - 80) / toc_line_height)
        toc_pages = max(1, (len(toc_entries) + toc_lines_per_page - 1) // toc_lines_per_page)

        # Simulate content pagination to compute page numbers for headings
        content_page_start = 1 + toc_pages + 1  # cover + toc + content
        heading_pages = {}
        cur_page = content_page_start
        cur_y = height - 40
        for line in lines:
            if cur_y < 40:
                cur_page += 1
                cur_y = height - 40
            if line.startswith("#"):
                title = line.lstrip("# ").strip()
                if line.startswith("## "):
                    heading_pages[title] = cur_page
                cur_y -= 16
            else:
                cur_y -= 12

        # Cover
        c.setFillColorRGB(0.1, 0.2, 0.35)
        c.rect(0, height - 180, width, 180, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont('Helvetica-Bold', 22)
        c.drawString(40, height - 80, 'ABoroOffice')
        c.setFont('Helvetica', 12)
        c.drawString(40, height - 105, 'Hilfe-Handbuch')
        c.setFillColorRGB(0, 0, 0)
        c.setFont('Helvetica', 11)
        c.drawString(40, height - 220, settings_obj.company_name or 'ABoroOffice')
        c.setFont('Helvetica', 9)
        address = f"{settings_obj.company_address} · {settings_obj.company_postal_code} {settings_obj.company_city}"
        c.drawString(40, height - 235, address.strip())
        c.drawString(40, height - 248, settings_obj.company_email or '')
        c.setFont('Helvetica', 9)
        c.drawString(40, 50, f"Version: {version_label} · Datum: {timezone.now().date()}")
        try:
            if settings_obj.logo and settings_obj.logo.path:
                c.drawImage(settings_obj.logo.path, width - 180, height - 120, width=120, height=50, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
        page_num = 1
        _footer(page_num)
        c.showPage()
        page_num += 1

        # TOC pages
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 40, "Inhaltsverzeichnis")
        c.setFont("Helvetica", 9)
        c.drawString(260, height - 40, "Seite")
        toc_y = height - 60
        for entry in toc_entries:
            if toc_y < 60:
                _footer(page_num)
                c.showPage()
                page_num += 1
                c.setFont("Helvetica-Bold", 14)
                c.drawString(40, height - 40, "Inhaltsverzeichnis")
                c.setFont("Helvetica", 9)
                c.drawString(260, height - 40, "Seite")
                toc_y = height - 60
            c.setFont("Helvetica", 9)
            c.drawString(40, toc_y, entry)
            c.drawString(260, toc_y, str(heading_pages.get(entry, content_page_start)))
            toc_y -= toc_line_height
        _footer(page_num)
        c.showPage()
        page_num += 1

        # Content pages
        y = height - 40
        c.setFont('Helvetica', 10)
        for line in lines:
            if y < 40:
                _footer(page_num)
                c.showPage()
                page_num += 1
                y = height - 40
                c.setFont('Helvetica', 10)
            if line.startswith('#'):
                c.setFont('Helvetica-Bold', 12)
                c.drawString(40, y, line.lstrip('# ').strip())
                y -= 16
                c.setFont('Helvetica', 10)
                continue
            c.drawString(40, y, line[:120])
            y -= 12
        _footer(page_num)
        c.save()
        return resp




