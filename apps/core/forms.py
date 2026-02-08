from django import forms
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


APP_TOGGLE_FIELDS = [
    ('approvals', 'SSH Approvals'),
    ('helpdesk', 'Helpdesk'),
    ('cloudstorage', 'CloudStorage'),
    ('classroom', 'Classroom'),
    ('crm', 'CRM'),
    ('contracts', 'Contracts'),
    ('marketing', 'Marketing'),
    ('erp', 'ERP'),
    ('projects', 'Projects'),
    ('workflows', 'Workflows'),
]

CRM_FALLBACK_PROVIDERS = [
    ('serpapi', 'SerpAPI (Google Search)'),
    ('dataforseo', 'DataForSEO (Google SERP)'),
    ('bing', 'Bing Web Search API'),
]

CRM_ENRICHMENT_PROVIDERS = [
    ('hunter', 'Hunter.io'),
    ('dropcontact', 'Dropcontact'),
    ('clearbit', 'Clearbit'),
]

class ThemeSettingsForm(forms.ModelForm):
    """Theme settings used for the global Admin Dashboard."""

    class Meta:
        model = SystemSettings
        fields = [
            'theme_variant',
            'primary_color',
            'secondary_color',
            'accent_color',
            'danger_color',
            'font_family',
            'border_radius',
            'enable_dark_mode',
        ]
        widgets = {
            'theme_variant': forms.Select(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'danger_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'font_family': forms.Select(attrs={'class': 'form-control'}),
            'border_radius': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '20'}),
            'enable_dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BrandingSettingsForm(forms.ModelForm):
    """Branding settings for the global Admin Dashboard."""

    class Meta:
        model = SystemSettings
        fields = [
            'app_name',
            'company_name',
            'company_address',
            'company_postal_code',
            'company_city',
            'company_country',
            'company_version',
            'company_email',
            'company_bank_name',
            'company_iban',
            'company_bic',
            'logo',
            'site_url',
        ]
        widgets = {
            'app_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.TextInput(attrs={'class': 'form-control'}),
            'company_postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'company_city': forms.TextInput(attrs={'class': 'form-control'}),
            'company_country': forms.TextInput(attrs={'class': 'form-control'}),
            'company_version': forms.TextInput(attrs={'class': 'form-control'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company_bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_iban': forms.TextInput(attrs={'class': 'form-control'}),
            'company_bic': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'site_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class AppTogglesForm(forms.Form):
    """Toggle access to apps globally."""

    approvals = forms.BooleanField(label='SSH Approvals', required=False)
    helpdesk = forms.BooleanField(label='Helpdesk', required=False)
    cloudstorage = forms.BooleanField(label='CloudStorage', required=False)
    classroom = forms.BooleanField(label='Classroom', required=False)
    crm = forms.BooleanField(label='CRM', required=False)
    contracts = forms.BooleanField(label='Contracts', required=False)
    marketing = forms.BooleanField(label='Marketing', required=False)
    erp = forms.BooleanField(label='ERP', required=False)
    personnel = forms.BooleanField(label='Personal', required=False)
    fibu = forms.BooleanField(label='FiBu', required=False)
    projects = forms.BooleanField(label='Projects', required=False)
    workflows = forms.BooleanField(label='Workflows', required=False)

    def __init__(self, *args, **kwargs):
        settings_obj = kwargs.pop('system_settings', None)
        super().__init__(*args, **kwargs)
        toggles = {}
        if settings_obj:
            toggles = settings_obj.app_toggles or {}
        self.fields['approvals'].initial = toggles.get('approvals', False)
        self.fields['helpdesk'].initial = toggles.get('helpdesk', True)
        self.fields['cloudstorage'].initial = toggles.get('cloudstorage', True)
        self.fields['classroom'].initial = toggles.get('classroom', True)
        self.fields['crm'].initial = toggles.get('crm', False)
        self.fields['contracts'].initial = toggles.get('contracts', False)
        self.fields['marketing'].initial = toggles.get('marketing', False)
        self.fields['erp'].initial = toggles.get('erp', False)
        self.fields['personnel'].initial = toggles.get('personnel', False)
        self.fields['fibu'].initial = toggles.get('fibu', False)
        self.fields['projects'].initial = toggles.get('projects', False)
        self.fields['workflows'].initial = toggles.get('workflows', False)


class DashboardSettingsForm(forms.ModelForm):
    """Dashboard layout settings."""

    class Meta:
        model = SystemSettings
        fields = [
            'plugin_dashboard_position',
        ]
        widgets = {
            'plugin_dashboard_position': forms.Select(attrs={'class': 'form-control'}),
        }


class CRMFallbackSettingsForm(forms.ModelForm):
    """CRM fallback provider settings."""

    crm_fallback_provider_order = forms.CharField(
        label='Provider-Reihenfolge',
        required=False,
        help_text='Kommagetrennt, z.B. serpapi,dataforseo,bing',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = SystemSettings
        fields = [
            'crm_fallback_enabled',
            'crm_fallback_provider_order',
            'crm_serpapi_key',
            'crm_dataforseo_login',
            'crm_dataforseo_password',
            'crm_bing_api_key',
        ]
        widgets = {
            'crm_fallback_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'crm_serpapi_key': forms.PasswordInput(attrs={'class': 'form-control'}),
            'crm_dataforseo_login': forms.TextInput(attrs={'class': 'form-control'}),
            'crm_dataforseo_password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'crm_bing_api_key': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        order = []
        if self.instance and self.instance.crm_fallback_provider_order:
            order = self.instance.crm_fallback_provider_order
        if isinstance(order, list) and order:
            self.fields['crm_fallback_provider_order'].initial = ",".join(order)

    def clean_crm_fallback_provider_order(self):
        raw = (self.cleaned_data.get('crm_fallback_provider_order') or "").strip()
        if not raw:
            return []
        tokens = [t.strip().lower() for t in raw.split(",") if t.strip()]
        allowed = {c[0] for c in CRM_FALLBACK_PROVIDERS}
        invalid = [t for t in tokens if t not in allowed]
        if invalid:
            raise forms.ValidationError(f"Ungültige Provider: {', '.join(invalid)}")
        return tokens


class CRMEnrichmentSettingsForm(forms.ModelForm):
    """CRM enrichment API settings (optional)."""

    crm_enrichment_provider_order = forms.CharField(
        label='Provider-Reihenfolge',
        required=False,
        help_text='Kommagetrennt, z.B. hunter,dropcontact,clearbit',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = SystemSettings
        fields = [
            'crm_enrichment_enabled',
            'crm_enrichment_provider_order',
            'crm_hunter_api_key',
            'crm_dropcontact_api_key',
            'crm_clearbit_api_key',
        ]
        widgets = {
            'crm_enrichment_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'crm_hunter_api_key': forms.PasswordInput(attrs={'class': 'form-control'}),
            'crm_dropcontact_api_key': forms.PasswordInput(attrs={'class': 'form-control'}),
            'crm_clearbit_api_key': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        order = []
        if self.instance and self.instance.crm_enrichment_provider_order:
            order = self.instance.crm_enrichment_provider_order
        if isinstance(order, list) and order:
            self.fields['crm_enrichment_provider_order'].initial = ",".join(order)

    def clean_crm_enrichment_provider_order(self):
        raw = (self.cleaned_data.get('crm_enrichment_provider_order') or "").strip()
        if not raw:
            return []
        tokens = [t.strip().lower() for t in raw.split(",") if t.strip()]
        allowed = {c[0] for c in CRM_ENRICHMENT_PROVIDERS}
        invalid = [t for t in tokens if t not in allowed]
        if invalid:
            raise forms.ValidationError(f"Ungültige Provider: {', '.join(invalid)}")
        return tokens


class DunningSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'dunning_enabled',
            'dunning_days_level1',
            'dunning_days_level2',
            'dunning_days_level3',
            'dunning_auto_send',
        ]
        widgets = {
            'dunning_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dunning_days_level1': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'dunning_days_level2': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'dunning_days_level3': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'dunning_auto_send': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InvoiceSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'invoice_auto_send',
            'invoice_payment_days',
            'invoice_email_subject_template',
            'invoice_email_body_template',
            'dunning_email_subject_template',
            'dunning_email_body_template',
        ]
        widgets = {
            'invoice_auto_send': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'invoice_payment_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'invoice_email_subject_template': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_email_body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'dunning_email_subject_template': forms.TextInput(attrs={'class': 'form-control'}),
            'dunning_email_body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class EmailLogSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'email_log_auto_archive_days',
        ]
        widgets = {
            'email_log_auto_archive_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class SchedulerSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'scheduler_enabled',
            'scheduler_mode',
            'scheduler_daily_time',
            'scheduler_interval_minutes',
        ]
        widgets = {
            'scheduler_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scheduler_mode': forms.Select(attrs={'class': 'form-select'}),
            'scheduler_daily_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'scheduler_interval_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '5'}),
        }


class MarketingRolesForm(forms.ModelForm):
    """Marketing group permissions (comma-separated)."""

    marketing_view_groups = forms.CharField(
        label='View-Gruppen',
        required=False,
        help_text='Kommagetrennt, z.B. Orga,Manager',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    marketing_edit_groups = forms.CharField(
        label='Edit-Gruppen',
        required=False,
        help_text='Kommagetrennt, z.B. Manager',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    marketing_approve_groups = forms.CharField(
        label='Approve-Gruppen',
        required=False,
        help_text='Kommagetrennt, z.B. Orga,Manager',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = SystemSettings
        fields = [
            'marketing_view_groups',
            'marketing_edit_groups',
            'marketing_approve_groups',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['marketing_view_groups'].initial = ",".join(self.instance.marketing_view_groups or [])
            self.fields['marketing_edit_groups'].initial = ",".join(self.instance.marketing_edit_groups or [])
            self.fields['marketing_approve_groups'].initial = ",".join(self.instance.marketing_approve_groups or [])

    def _clean_groups(self, value):
        raw = (value or "").strip()
        if not raw:
            return []
        return [v.strip() for v in raw.split(",") if v.strip()]

    def clean_marketing_view_groups(self):
        return self._clean_groups(self.cleaned_data.get('marketing_view_groups'))

    def clean_marketing_edit_groups(self):
        return self._clean_groups(self.cleaned_data.get('marketing_edit_groups'))

    def clean_marketing_approve_groups(self):
        return self._clean_groups(self.cleaned_data.get('marketing_approve_groups'))


class ErpRolesForm(forms.ModelForm):
    """ERP group permissions (comma-separated)."""

    erp_view_groups = forms.CharField(
        label='View-Gruppen',
        required=False,
        help_text='Kommagetrennt, z.B. Orga,Manager',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    erp_edit_groups = forms.CharField(
        label='Edit-Gruppen',
        required=False,
        help_text='Kommagetrennt, z.B. Manager',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = SystemSettings
        fields = [
            'erp_view_groups',
            'erp_edit_groups',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['erp_view_groups'].initial = ",".join(self.instance.erp_view_groups or [])
            self.fields['erp_edit_groups'].initial = ",".join(self.instance.erp_edit_groups or [])

    def _clean_groups(self, value):
        raw = (value or "").strip()
        if not raw:
            return []
        return [v.strip() for v in raw.split(",") if v.strip()]

    def clean_erp_view_groups(self):
        return self._clean_groups(self.cleaned_data.get('erp_view_groups'))

    def clean_erp_edit_groups(self):
        return self._clean_groups(self.cleaned_data.get('erp_edit_groups'))


class ErpPricingForm(forms.ModelForm):
    """ERP pricing settings."""

    class Meta:
        model = SystemSettings
        fields = [
            'erp_min_margin_pct',
            'erp_undercut_min_pct',
            'erp_undercut_max_pct',
        ]
        widgets = {
            'erp_min_margin_pct': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'erp_undercut_min_pct': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'erp_undercut_max_pct': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ErpCompetitorForm(forms.ModelForm):
    """ERP competitor provider settings."""

    erp_competitor_provider = forms.ChoiceField(
        choices=[
            ('manual', 'Manuell (kein Abruf)'),
            ('geizhals', 'Geizhals (Scraper)'),
            ('api', 'Custom API'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = SystemSettings
        fields = [
            'erp_competitor_scrape_enabled',
            'erp_competitor_provider',
            'erp_competitor_api_url',
            'erp_competitor_api_key',
            'erp_competitor_accept_terms',
        ]
        widgets = {
            'erp_competitor_scrape_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'erp_competitor_api_url': forms.URLInput(attrs={'class': 'form-control'}),
            'erp_competitor_api_key': forms.TextInput(attrs={'class': 'form-control'}),
            'erp_competitor_accept_terms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BedrockSettingsForm(forms.ModelForm):
    """Bedrock configuration."""

    class Meta:
        model = SystemSettings
        fields = [
            'bedrock_enabled',
            'bedrock_api_key',
            'bedrock_region',
            'bedrock_model_id',
            'bedrock_max_tokens',
            'bedrock_temperature',
        ]
        widgets = {
            'bedrock_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bedrock_api_key': forms.PasswordInput(attrs={'class': 'form-control'}),
            'bedrock_region': forms.TextInput(attrs={'class': 'form-control'}),
            'bedrock_model_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bedrock_max_tokens': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'bedrock_temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }

