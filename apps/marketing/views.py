from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, View
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from collections import defaultdict
from .models import Campaign, ContentAsset, ContentIdea, ContentApproval, ContentRevision, CampaignKpiSnapshot
from .forms import CampaignForm, ContentAssetForm, ContentIdeaForm, ApprovalForm
from .services.ai import MarketingAIService
from .permissions import (
    MarketingViewMixin,
    MarketingEditMixin,
    can_edit_marketing,
    can_approve_marketing,
)
import csv
from io import TextIOWrapper


CHANNEL_TEMPLATES = {
    "linkedin": {
        "label": "LinkedIn Post",
        "content": (
            "🚀 {Thema/Hook}\n\n"
            "Problem: {Problem kurz benennen}\n"
            "Lösung: {Wie wir helfen}\n"
            "Ergebnis: {Benefit/Outcome}\n\n"
            "👉 CTA: {Kontakt/Call-to-Action}\n"
            "#Hashtags"
        ),
    },
    "newsletter": {
        "label": "Newsletter",
        "content": (
            "Betreff: {Betreff}\n\n"
            "Hallo {Name/Team},\n\n"
            "Kurzer Überblick: {Zusammenfassung}\n"
            "- Punkt 1: {Mehrwert}\n"
            "- Punkt 2: {Mehrwert}\n"
            "- Punkt 3: {Mehrwert}\n\n"
            "CTA: {Link oder Antwortaufforderung}\n\n"
            "Viele Grüße\n{Absender}"
        ),
    },
    "blog": {
        "label": "Blog Artikel",
        "content": (
            "# {Titel}\n\n"
            "## Einleitung\n{Hook + Problem}\n\n"
            "## Hauptteil\n- Abschnitt 1: {Kernidee}\n- Abschnitt 2: {Beispiele}\n- Abschnitt 3: {Tipps}\n\n"
            "## Fazit\n{Zusammenfassung + CTA}\n"
        ),
    },
    "ad": {
        "label": "Anzeige",
        "content": (
            "{Headline}\n"
            "{Subline}\n"
            "{Benefit}\n"
            "CTA: {Jetzt testen/kontaktieren}\n"
        ),
    },
}


def _min_length_for(asset_type: str) -> int:
    return {
        "blog": 400,
        "newsletter": 200,
        "landing": 300,
        "social": 80,
        "ad": 40,
    }.get(asset_type, 80)


def _run_preflight_checks(asset: ContentAsset) -> list:
    issues = []
    content = (asset.content or "").strip()
    if not content:
        issues.append("Content ist leer.")
    if len(content) < _min_length_for(asset.asset_type):
        issues.append("Content zu kurz für den gewählten Typ.")
    channel = (asset.channel or "").lower()
    if "linkedin" in channel and "#" not in content:
        issues.append("LinkedIn: Hashtags fehlen.")
    if "newsletter" in channel and ("betreff:" not in content.lower() and "subject:" not in content.lower()):
        issues.append("Newsletter: Betreff fehlt (z.B. 'Betreff: ...').")
    if asset.asset_type == "ad" and len(content) > 300:
        issues.append("Anzeige: Content zu lang.")
    cta_keywords = ["jetzt", "kontakt", "buchen", "angebot", "mehr erfahren", "kostenlos", "demo"]
    if not any(k in content.lower() for k in cta_keywords):
        issues.append("CTA fehlt (z.B. 'Jetzt', 'Kontakt', 'Mehr erfahren').")
    return issues


def _parse_number(value, is_int=False):
    if value is None:
        return 0
    text = str(value).strip().replace(".", "").replace(",", ".")
    if not text:
        return 0
    try:
        return int(float(text)) if is_int else float(text)
    except Exception:
        return 0


def _parse_kpi_csv(upload):
    totals = {
        "impressions": 0,
        "clicks": 0,
        "conversions": 0,
        "spend": 0.0,
        "revenue": 0.0,
    }
    wrapped = TextIOWrapper(upload.file, encoding="utf-8", errors="ignore")
    reader = csv.DictReader(wrapped)
    for row in reader:
        normalized = {str(k).strip().lower(): v for k, v in row.items()}
        totals["impressions"] += _parse_number(normalized.get("impressions") or normalized.get("impr"), is_int=True)
        totals["clicks"] += _parse_number(normalized.get("clicks"), is_int=True)
        totals["conversions"] += _parse_number(
            normalized.get("conversions") or normalized.get("conv") or normalized.get("leads"),
            is_int=True,
        )
        totals["spend"] += _parse_number(normalized.get("spend") or normalized.get("cost"))
        totals["revenue"] += _parse_number(normalized.get("revenue") or normalized.get("value"))
    return totals


def _validate_kpi_csv(upload):
    wrapped = TextIOWrapper(upload.file, encoding="utf-8", errors="ignore")
    reader = csv.DictReader(wrapped)
    headers = [str(h).strip().lower() for h in (reader.fieldnames or [])]
    required = {"impressions", "clicks", "conversions", "spend", "revenue"}
    missing = [h for h in required if h not in headers]
    return missing


def _kpi_delta(current, previous):
    try:
        return current - previous
    except Exception:
        return 0


def _chart_data_for_campaign(campaign: Campaign):
    values = [
        ("Impressions", int(campaign.kpi_impressions)),
        ("Clicks", int(campaign.kpi_clicks)),
        ("Conversions", int(campaign.kpi_conversions)),
        ("Spend", float(campaign.kpi_spend)),
        ("Revenue", float(campaign.kpi_revenue)),
    ]
    max_value = max([v for _, v in values] or [1])
    chart = []
    for label, value in values:
        percent = 0
        if max_value:
            percent = round((value / max_value) * 100, 2)
        chart.append({"label": label, "value": value, "percent": percent})
    return chart


def _trend_values_for_snapshots(snapshots, metric):
    values = []
    for snap in snapshots:
        values.append(getattr(snap, metric, 0) or 0)
    max_value = max(values or [1])
    min_value = min(values or [0])
    points = []
    for snap in snapshots:
        value = getattr(snap, metric, 0) or 0
        percent = 0
        if max_value:
            percent = round((value / max_value) * 100, 2)
        points.append({
            "date": snap.imported_at.date(),
            "value": value,
            "percent": percent,
        })
    delta = 0
    if len(values) >= 2:
        delta = values[-1] - values[-2]
    return points, min_value, max_value, delta


class MarketingHomeView(MarketingViewMixin, TemplateView):
    template_name = 'marketing/home.html'


class CampaignListView(MarketingViewMixin, ListView):
    model = Campaign
    template_name = 'marketing/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 25

    def get_queryset(self):
        return Campaign.objects.all().order_by('-updated_at')


class CampaignCreateView(MarketingEditMixin, CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'marketing/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Kampagne erstellen'
        return context

    def get_success_url(self):
        return reverse('marketing:campaign_list')


class CampaignUpdateView(MarketingEditMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'marketing/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Kampagne bearbeiten'
        return context

    def get_success_url(self):
        return reverse('marketing:campaign_list')


class CampaignDetailView(MarketingViewMixin, DetailView):
    model = Campaign
    template_name = 'marketing/campaign_detail.html'
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assets'] = ContentAsset.objects.filter(campaign=self.object).order_by('-updated_at')[:10]
        context['kpi_delta'] = {
            "impressions": _kpi_delta(self.object.kpi_impressions, self.object.last_kpi_impressions),
            "clicks": _kpi_delta(self.object.kpi_clicks, self.object.last_kpi_clicks),
            "conversions": _kpi_delta(self.object.kpi_conversions, self.object.last_kpi_conversions),
            "spend": _kpi_delta(float(self.object.kpi_spend), float(self.object.last_kpi_spend)),
            "revenue": _kpi_delta(float(self.object.kpi_revenue), float(self.object.last_kpi_revenue)),
        }
        context['kpi_chart'] = _chart_data_for_campaign(self.object)
        metric = self.request.GET.get('trend', 'clicks').lower()
        if metric not in ['clicks', 'impressions', 'revenue']:
            metric = 'clicks'
        snapshots = list(self.object.kpi_snapshots.order_by('-imported_at')[:7])[::-1]
        context['trend_metric'] = metric
        points, min_value, max_value, delta = _trend_values_for_snapshots(snapshots, metric)
        context['kpi_sparkline'] = points
        context['kpi_trend_min'] = min_value
        context['kpi_trend_max'] = max_value
        context['kpi_trend_delta'] = delta
        context['kpi_snapshots'] = snapshots
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_marketing(request.user):
            messages.error(request, 'Keine Berechtigung für diese Aktion.')
            return redirect(reverse('marketing:campaign_detail', args=[self.object.pk]))
        action = request.POST.get('action')
        if action == 'import_kpi':
            upload = request.FILES.get('kpi_file')
            if not upload:
                messages.error(request, 'Bitte CSV-Datei auswählen.')
                return redirect(reverse('marketing:campaign_detail', args=[self.object.pk]))
            try:
                missing = _validate_kpi_csv(upload)
                upload.seek(0)
                if missing:
                    messages.error(request, f"CSV fehlt Spalten: {', '.join(sorted(missing))}")
                    return redirect(reverse('marketing:campaign_detail', args=[self.object.pk]))
                self.object.last_kpi_impressions = self.object.kpi_impressions
                self.object.last_kpi_clicks = self.object.kpi_clicks
                self.object.last_kpi_conversions = self.object.kpi_conversions
                self.object.last_kpi_spend = self.object.kpi_spend
                self.object.last_kpi_revenue = self.object.kpi_revenue
                totals = _parse_kpi_csv(upload)
                self.object.kpi_impressions = totals["impressions"]
                self.object.kpi_clicks = totals["clicks"]
                self.object.kpi_conversions = totals["conversions"]
                self.object.kpi_spend = totals["spend"]
                self.object.kpi_revenue = totals["revenue"]
                self.object.last_kpi_imported_at = timezone.now()
                self.object.save(update_fields=[
                    'kpi_impressions',
                    'kpi_clicks',
                    'kpi_conversions',
                    'kpi_spend',
                    'kpi_revenue',
                    'last_kpi_impressions',
                    'last_kpi_clicks',
                    'last_kpi_conversions',
                    'last_kpi_spend',
                    'last_kpi_revenue',
                    'last_kpi_imported_at',
                    'updated_at',
                ])
                CampaignKpiSnapshot.objects.create(
                    campaign=self.object,
                    impressions=self.object.kpi_impressions,
                    clicks=self.object.kpi_clicks,
                    conversions=self.object.kpi_conversions,
                    spend=self.object.kpi_spend,
                    revenue=self.object.kpi_revenue,
                    imported_at=self.object.last_kpi_imported_at,
                )
                messages.success(request, 'KPIs importiert.')
            except Exception as exc:
                messages.error(request, f'KPI-Import fehlgeschlagen: {exc}')
        return redirect(reverse('marketing:campaign_detail', args=[self.object.pk]))


class MarketingKpiTemplateView(MarketingViewMixin, View):
    def get(self, request, *args, **kwargs):
        content = "impressions,clicks,conversions,spend,revenue\n"
        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="kpi_template.csv"'
        return response


class MarketingKpiExportView(MarketingViewMixin, View):
    def get(self, request, pk, *args, **kwargs):
        campaign = Campaign.objects.get(pk=pk)
        content = "impressions,clicks,conversions,spend,revenue\n"
        content += f"{campaign.kpi_impressions},{campaign.kpi_clicks},{campaign.kpi_conversions},{campaign.kpi_spend},{campaign.kpi_revenue}\n"
        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="kpi_snapshot_{campaign.id}.csv"'
        return response


class AssetListView(MarketingViewMixin, ListView):
    model = ContentAsset
    template_name = 'marketing/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 25

    def get_queryset(self):
        return ContentAsset.objects.select_related('campaign').all().order_by('-updated_at')


class AssetDetailView(MarketingViewMixin, DetailView):
    model = ContentAsset
    template_name = 'marketing/asset_detail.html'
    context_object_name = 'asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = can_edit_marketing(self.request.user)
        context['can_approve'] = can_approve_marketing(self.request.user)
        context['revisions'] = self.object.revisions.order_by('-stamped_at')[:10]
        return context

    def post(self, request, *args, **kwargs):
        if not can_edit_marketing(request.user) and request.POST.get('action') not in ['apply_approval']:
            messages.error(request, 'Keine Berechtigung für diese Aktion.')
            return redirect(reverse('marketing:asset_detail', args=[self.get_object().pk]))
        self.object = self.get_object()
        action = request.POST.get('action')
        if action == 'save_brief':
            brief = request.POST.get('brief', '').strip()
            self.object.brief = brief
            self.object.status = 'draft'
            self.object.save(update_fields=['brief', 'status', 'updated_at'])
            messages.success(request, 'Briefing gespeichert.')
            return redirect(reverse('marketing:asset_detail', args=[self.object.pk]))
        if action == 'apply_template':
            template_key = request.POST.get('template_key', '').strip()
            template = CHANNEL_TEMPLATES.get(template_key)
            if template:
                if not self.object.content:
                    self.object.content = template["content"]
                else:
                    self.object.content = f"{template['content']}\n\n{self.object.content}"
                self.object.save(update_fields=['content', 'updated_at'])
                messages.success(request, f"Template '{template['label']}' angewendet.")
            else:
                messages.error(request, 'Template nicht gefunden.')
            return redirect(reverse('marketing:asset_detail', args=[self.object.pk]))
        if action == 'generate_content':
            brief = request.POST.get('brief', '').strip() or self.object.brief
            if not brief:
                messages.error(request, 'Bitte ein Briefing eingeben.')
                return redirect(reverse('marketing:asset_detail', args=[self.object.pk]))
            try:
                ai = MarketingAIService()
                data = ai.generate_content(self.object.asset_type, self.object.channel, brief)
                self.object.title = data.get('title') or self.object.title
                self.object.content = data.get('content') or self.object.content
                self.object.status = 'draft'
                self.object.save(update_fields=['title', 'content', 'status', 'updated_at'])
                messages.success(request, 'Content generiert.')
            except Exception as exc:
                messages.error(request, f'AI Fehler: {exc}')
        elif action == 'request_approval':
            issues = _run_preflight_checks(self.object)
            if issues:
                for issue in issues:
                    messages.error(request, f"Prüfliste: {issue}")
                return redirect(reverse('marketing:asset_detail', args=[self.object.pk]))
            ContentApproval.objects.create(
                asset=self.object,
                requested_by=request.user,
                status='pending',
            )
            self.object.status = 'review'
            self.object.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Freigabe angefordert.')
        elif action == 'publish':
            self.object.status = 'published'
            if not self.object.scheduled_at:
                self.object.scheduled_at = timezone.now()
            self.object.save(update_fields=['status', 'scheduled_at', 'updated_at'])
            ContentRevision.objects.create(
                asset=self.object,
                title=self.object.title,
                content=self.object.content,
                action='published',
                note='Veröffentlicht',
                stamped_by=request.user,
            )
            messages.success(request, 'Content veröffentlicht.')
        elif action == 'apply_approval':
            if not can_approve_marketing(request.user):
                messages.error(request, 'Keine Freigabe-Berechtigung.')
                return redirect(reverse('marketing:asset_detail', args=[self.object.pk]))
            form = ApprovalForm(request.POST)
            if form.is_valid():
                approval = form.save(commit=False)
                approval.asset = self.object
                approval.reviewed_by = request.user
                approval.reviewed_at = timezone.now()
                approval.save()
                if approval.status == 'approved':
                    self.object.status = 'approved'
                    ContentRevision.objects.create(
                        asset=self.object,
                        title=self.object.title,
                        content=self.object.content,
                        action='approved',
                        note=approval.note or '',
                        stamped_by=request.user,
                    )
                elif approval.status == 'rejected':
                    self.object.status = 'draft'
                    ContentRevision.objects.create(
                        asset=self.object,
                        title=self.object.title,
                        content=self.object.content,
                        action='rejected',
                        note=approval.note or '',
                        stamped_by=request.user,
                    )
                self.object.save(update_fields=['status', 'updated_at'])
                messages.success(request, 'Freigabe gespeichert.')
        return redirect(reverse('marketing:asset_detail', args=[self.object.pk]))


class AssetCreateView(MarketingEditMixin, CreateView):
    model = ContentAsset
    form_class = ContentAssetForm
    template_name = 'marketing/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Content erstellen'
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
        return redirect(reverse('marketing:asset_detail', args=[obj.pk]))


class AssetUpdateView(MarketingEditMixin, UpdateView):
    model = ContentAsset
    form_class = ContentAssetForm
    template_name = 'marketing/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Content bearbeiten'
        return context

    def get_success_url(self):
        return reverse('marketing:asset_detail', args=[self.object.pk])


class IdeaListView(MarketingViewMixin, ListView):
    model = ContentIdea
    template_name = 'marketing/idea_list.html'
    context_object_name = 'ideas'
    paginate_by = 25

    def get_queryset(self):
        return ContentIdea.objects.all().order_by('-created_at')

    def post(self, request, *args, **kwargs):
        topic = request.POST.get('topic', '').strip()
        if topic:
            try:
                ai = MarketingAIService()
                ideas = ai.generate_ideas(topic)
                for idea in ideas:
                    ContentIdea.objects.create(title=idea, created_by=request.user)
                messages.success(request, 'Ideen generiert.')
            except Exception as exc:
                messages.error(request, f'AI Fehler: {exc}')
        return redirect('marketing:idea_list')


class IdeaCreateView(MarketingEditMixin, CreateView):
    model = ContentIdea
    form_class = ContentIdeaForm
    template_name = 'marketing/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Idee erstellen'
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
        return redirect('marketing:idea_list')


class MarketingCalendarView(MarketingViewMixin, TemplateView):
    template_name = 'marketing/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start = timezone.now() - timezone.timedelta(days=7)
        end = timezone.now() + timezone.timedelta(days=30)
        assets = (
            ContentAsset.objects
            .filter(scheduled_at__isnull=False, scheduled_at__range=(start, end))
            .order_by('scheduled_at')
        )
        grouped = defaultdict(list)
        for asset in assets:
            date_key = asset.scheduled_at.date()
            grouped[date_key].append(asset)
        context['calendar_groups'] = sorted(grouped.items(), key=lambda x: x[0])
        context['calendar_start'] = start.date()
        context['calendar_end'] = end.date()
        return context


class MarketingHelpView(MarketingViewMixin, TemplateView):
    template_name = 'marketing/help.html'
