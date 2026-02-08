from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now as timezone_now
import json
from apps.helpdesk.helpdesk_apps.api.license_manager import LicenseManager


class SystemSettings(models.Model):
    """System-wide settings managed through admin panel"""

    # Email Configuration (SMTP)
    smtp_host = models.CharField(_('SMTP Host'), max_length=255, default='smtp.office365.com',
                                help_text='e.g., smtp.office365.com, smtp.gmail.com')
    smtp_port = models.IntegerField(_('SMTP Port'), default=587)
    smtp_username = models.CharField(_('SMTP Username'), max_length=255, blank=True)
    smtp_password = models.CharField(_('SMTP Password'), max_length=255, blank=True)
    smtp_use_tls = models.BooleanField(_('Use TLS'), default=True)
    smtp_use_ssl = models.BooleanField(_('Use SSL'), default=False)

    # IMAP Configuration (for email import)
    imap_enabled = models.BooleanField(_('Enable IMAP'), default=False,
                                      help_text='Enable reading emails from mailbox')
    imap_host = models.CharField(_('IMAP Host'), max_length=255, default='outlook.office365.com',
                                blank=True)
    imap_port = models.IntegerField(_('IMAP Port'), default=993, blank=True)
    imap_username = models.CharField(_('IMAP Username'), max_length=255, blank=True)
    imap_password = models.CharField(_('IMAP Password'), max_length=255, blank=True)
    imap_use_ssl = models.BooleanField(_('Use SSL'), default=True)
    imap_folder = models.CharField(_('IMAP Folder'), max_length=255, default='INBOX',
                                  help_text='Mailbox folder to monitor')
    imap_last_sync = models.DateTimeField(_('Last Email Sync'), null=True, blank=True,
                                         help_text='Timestamp of last successful email synchronization')
    imap_full_sync_completed = models.BooleanField(_('Full Sync Completed'), default=False,
                                                  help_text='Whether initial full mailbox sync has been completed')

    # Branding Configuration
    logo = models.ImageField(_('Logo'), upload_to='logos/', null=True, blank=True,
                            help_text='Company logo (max 2MB, recommended: 200x50px)')
    app_name = models.CharField(_('Application Name'), max_length=255, default='Helpdesk',
                               help_text='Name shown in navbar and browser tab')
    company_name = models.CharField(_('Company Name'), max_length=255, default='Company',
                                   help_text='Company name for branding')
    company_address = models.CharField(
        _('Company Address'),
        max_length=255,
        blank=True,
        help_text='Street and house number for outgoing letters'
    )
    company_postal_code = models.CharField(
        _('Company Postal Code'),
        max_length=20,
        blank=True,
        help_text='Postal code for outgoing letters'
    )
    company_city = models.CharField(
        _('Company City'),
        max_length=100,
        blank=True,
        help_text='City for outgoing letters'
    )
    company_country = models.CharField(
        _('Company Country'),
        max_length=100,
        blank=True,
        help_text='Country for outgoing letters'
    )
    company_version = models.CharField(
        _('Document Version'),
        max_length=50,
        default='1.0',
        help_text='Version for exported documents and guides.'
    )
    company_email = models.EmailField(
        _('Company Email'),
        blank=True,
        help_text='Sender email used for invoices and dunning'
    )
    company_bank_name = models.CharField(
        _('Company Bank'),
        max_length=255,
        blank=True,
        help_text='Bank name for payment details on invoices'
    )
    company_iban = models.CharField(
        _('Company IBAN'),
        max_length=64,
        blank=True,
        help_text='IBAN for payment details on invoices'
    )
    company_bic = models.CharField(
        _('Company BIC'),
        max_length=64,
        blank=True,
        help_text='BIC for payment details on invoices'
    )
    dunning_enabled = models.BooleanField(
        _('Enable Dunning'),
        default=True,
        help_text='Automatisches Mahnwesen aktivieren'
    )
    dunning_days_level1 = models.IntegerField(
        _('Days Overdue (Level 1)'),
        default=14,
        help_text='Tage nach Fälligkeit für Mahnstufe 1'
    )
    dunning_days_level2 = models.IntegerField(
        _('Days Overdue (Level 2)'),
        default=30,
        help_text='Tage nach Fälligkeit für Mahnstufe 2'
    )
    dunning_days_level3 = models.IntegerField(
        _('Days Overdue (Level 3)'),
        default=45,
        help_text='Tage nach Fälligkeit für Mahnstufe 3'
    )
    dunning_auto_send = models.BooleanField(
        _('Auto Send Dunning Emails'),
        default=False,
        help_text='Mahnungsmails automatisch versenden'
    )
    invoice_auto_send = models.BooleanField(
        _('Auto Send Invoice Emails'),
        default=False,
        help_text='Rechnungen automatisch per Scheduler versenden'
    )
    invoice_payment_days = models.IntegerField(
        _('Invoice Payment Days'),
        default=14,
        help_text='Zahlungsziel in Tagen (für Rechnungen)'
    )
    invoice_email_subject_template = models.CharField(
        _('Invoice Email Subject Template'),
        max_length=255,
        blank=True,
        help_text='z.B. "Rechnung {invoice_number} von {company_name}"'
    )
    invoice_email_body_template = models.TextField(
        _('Invoice Email Body Template'),
        blank=True,
        help_text='Platzhalter: {invoice_number}, {amount}, {due_date}, {customer_name}, {company_name}'
    )
    dunning_email_subject_template = models.CharField(
        _('Dunning Email Subject Template'),
        max_length=255,
        blank=True,
        help_text='z.B. "Mahnung {dunning_number} zu Rechnung {invoice_number}"'
    )
    dunning_email_body_template = models.TextField(
        _('Dunning Email Body Template'),
        blank=True,
        help_text='Platzhalter: {dunning_number}, {invoice_number}, {amount}, {due_date}, {customer_name}, {company_name}'
    )
    scheduler_enabled = models.BooleanField(
        _('Scheduler Enabled'),
        default=False,
        help_text='Aktiviert den Zeitplan für Rechnungen und Mahnungen'
    )
    scheduler_mode = models.CharField(
        _('Scheduler Mode'),
        max_length=20,
        choices=[('daily', 'Daily Time'), ('interval', 'Interval Minutes')],
        default='daily'
    )
    scheduler_daily_time = models.TimeField(
        _('Scheduler Daily Time'),
        null=True,
        blank=True,
        help_text='z.B. 08:00'
    )
    scheduler_interval_minutes = models.IntegerField(
        _('Scheduler Interval Minutes'),
        default=60,
        help_text='z.B. alle 60 Minuten'
    )
    scheduler_last_run = models.DateTimeField(
        _('Scheduler Last Run'),
        null=True,
        blank=True
    )
    email_log_auto_archive_days = models.IntegerField(
        _('Email Log Auto Archive Days'),
        default=30,
        help_text='E-Mails älter als X Tage automatisch archivieren'
    )
    site_url = models.URLField(_('Site URL'), default='http://localhost:8000',
                              help_text='Base URL for email links and redirects')

    # Text Editor Configuration
    text_editor = models.CharField(
        _('Text Editor'),
        max_length=20,
        choices=[
            ('tinymce', 'TinyMCE'),
            ('ckeditor', 'CKEditor'),
        ],
        default='tinymce',
        help_text='Choose which rich text editor to use throughout the application'
    )

    # Statistics Access Permissions (JSON storage for flexibility) - OPTIONAL
    stats_permissions = models.JSONField(
        _('Statistics Permissions (Optional)'),
        default=dict,
        blank=True,
        help_text='Erweiterte Statistik-Berechtigungen (optional, leer lassen falls nicht benötigt)'
    )

    # File Upload Settings
    max_upload_size_mb = models.IntegerField(_('Max Upload Size (MB)'), default=16,
                                            help_text='Maximum file size allowed for uploads')
    allowed_file_types = models.JSONField(
        _('Allowed File Types'),
        default=list,
        help_text='List of allowed file extensions (e.g., ["pdf", "jpg", "png"])'
    )

    # Email Notification Settings
    send_email_notifications = models.BooleanField(_('Send Email Notifications'), default=True)
    email_signature = models.TextField(_('Email Signature'), blank=True,
                                      help_text='Signature added to all outgoing emails')

    # License Configuration - SIMPLIFIED
    license_code = models.CharField(
        _('License Code'),
        max_length=255,
        blank=True,
        null=True,
        help_text='ABoro-Soft Helpdesk License Code - alle Features werden automatisch erkannt'
    )
    license_last_validated = models.DateTimeField(
        _('License Last Validated'),
        null=True,
        blank=True,
        help_text='When the license was last validated'
    )

    # AI Settings
    ai_enabled = models.BooleanField(
        _('AI Chat Support aktiviert'),
        default=False,
        help_text='KI-gestützte Antworten im Live Chat aktivieren'
    )
    ai_provider = models.CharField(
        _('AI Provider'),
        max_length=20,
        choices=[
            ('llama3', 'LLAMA3 (Lokal - kostenlos)'),
            ('chatgpt', 'ChatGPT (OpenAI)'),
            ('claude', 'Claude (Anthropic)'),
        ],
        default='llama3',
        help_text='Welche KI für automatische Antworten verwenden'
    )
    openai_api_key = models.CharField(
        _('OpenAI API Key'),
        max_length=255,
        blank=True,
        null=True,
        help_text='API Key für ChatGPT Integration'
    )
    anthropic_api_key = models.CharField(
        _('Anthropic API Key'),
        max_length=255,
        blank=True,
        null=True,
        help_text='API Key für Claude Integration (optional, nutzt sonst Free-Version)'
    )
    ai_response_delay = models.IntegerField(
        _('AI Antwort Verzögerung (Sekunden)'),
        default=3,
        help_text='Wartezeit bevor KI antwortet (um natürlicher zu wirken)'
    )
    ai_max_tokens = models.IntegerField(
        _('AI Max Tokens'),
        default=500,
        help_text='Maximale Länge der KI-Antworten'
    )

    # Theme Settings
    theme_variant = models.CharField(
        _('Theme Variant'),
        max_length=50,
        choices=[
            ('default', 'Default (Modern Blue)'),
            ('professional', 'Professional (Dark Blue)'),
            ('bright', 'Bright (Orange)'),
            ('modern', 'Modern (Indigo & Teal)'),
            ('corporate', 'Corporate (Navy Blue)'),
            ('dark', 'Dark Mode (Dark Gray & Blue)'),
            ('custom', 'Custom'),
        ],
        default='default',
        help_text='Vordefiniertes Theme oder Custom für Admin-Konfiguration'
    )
    primary_color = models.CharField(
        _('Primary Color'),
        max_length=7,
        default='#0066CC',
        help_text='Primärfarbe für Hauptelemente'
    )
    secondary_color = models.CharField(
        _('Secondary Color'),
        max_length=7,
        default='#00B366',
        help_text='Sekundärfarbe für Nebenelemente'
    )
    accent_color = models.CharField(
        _('Accent Color'),
        max_length=7,
        default='#FF6600',
        help_text='Akzentfarbe für wichtige CTAs'
    )
    danger_color = models.CharField(
        _('Danger Color'),
        max_length=7,
        default='#CC0000',
        help_text='Farbe für Warnungen und Fehler'
    )
    font_family = models.CharField(
        _('Font Family'),
        max_length=100,
        choices=[
            ('inter', 'Inter (Modern)'),
            ('roboto', 'Roboto (Standard)'),
            ('playfair', 'Playfair (Elegant)'),
            ('poppins', 'Poppins (Casual)'),
        ],
        default='inter',
        help_text='Schriftart für die Anwendung'
    )
    border_radius = models.IntegerField(
        _('Border Radius (px)'),
        default=8,
        help_text='Eckenradius für Cards und Buttons'
    )
    enable_dark_mode = models.BooleanField(
        _('Enable Dark Mode'),
        default=False,
        help_text='Dark Mode Umschalter aktivieren'
    )

    # System Settings
    timezone = models.CharField(_('Timezone'), max_length=100, default='Europe/Berlin')
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=[
            ('de', 'Deutsch'),
            ('en', 'English'),
        ],
        default='de'
    )

    # Metadata
    created_at = models.DateTimeField(_('Created At'), default=timezone_now)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_settings',
        verbose_name=_('Updated By')
    )

    # App Toggles (global)
    app_toggles = models.JSONField(
        _('App Toggles'),
        default=dict,
        blank=True,
        help_text='Enable/disable modules globally'
    )

    # Dashboard layout (global)
    plugin_dashboard_position = models.CharField(
        _('Plugin-Bereich Position'),
        max_length=20,
        choices=[
            ('top', 'Oben'),
            ('bottom', 'Unten'),
            ('left', 'Links'),
            ('right', 'Rechts'),
            ('center', 'Mitte'),
        ],
        default='bottom',
        help_text='Position des Plugin-Bereichs im Haupt-Dashboard'
    )

    # CRM Lead-Fallback Settings
    crm_fallback_enabled = models.BooleanField(
        _('CRM Fallback aktiviert'),
        default=False,
        help_text='Nutze Such-APIs als Notfall-Fallback, wenn die Primärquelle 0 Treffer liefert'
    )
    crm_fallback_provider_order = models.JSONField(
        _('CRM Fallback Provider (Reihenfolge)'),
        default=list,
        blank=True,
        help_text='Beispiel: ["serpapi", "dataforseo", "bing"]'
    )
    crm_serpapi_key = models.CharField(
        _('SerpAPI Key'),
        max_length=255,
        blank=True,
        help_text='API Key für SerpAPI (Google Search)'
    )
    crm_dataforseo_login = models.CharField(
        _('DataForSEO Login'),
        max_length=255,
        blank=True,
        help_text='Login (E-Mail) für DataForSEO'
    )
    crm_dataforseo_password = models.CharField(
        _('DataForSEO Password'),
        max_length=255,
        blank=True,
        help_text='Passwort für DataForSEO'
    )
    crm_bing_api_key = models.CharField(
        _('Bing Search API Key'),
        max_length=255,
        blank=True,
        help_text='API Key für Microsoft Bing Web Search'
    )

    # CRM Enrichment API Settings (optional)
    crm_enrichment_enabled = models.BooleanField(
        _('CRM Enrichment aktiviert'),
        default=False,
        help_text='Optionale Enrichment-APIs für E-Mail/Domain-Daten aktivieren'
    )
    crm_enrichment_provider_order = models.JSONField(
        _('CRM Enrichment Provider (Reihenfolge)'),
        default=list,
        blank=True,
        help_text='Beispiel: ["hunter", "dropcontact", "clearbit"]'
    )
    crm_hunter_api_key = models.CharField(
        _('Hunter API Key'),
        max_length=255,
        blank=True,
        help_text='API Key für Hunter.io'
    )
    crm_dropcontact_api_key = models.CharField(
        _('Dropcontact API Key'),
        max_length=255,
        blank=True,
        help_text='API Key für Dropcontact'
    )
    crm_clearbit_api_key = models.CharField(
        _('Clearbit API Key'),
        max_length=255,
        blank=True,
        help_text='API Key für Clearbit'
    )

    # Marketing Permissions (group-based)
    marketing_view_groups = models.JSONField(
        _('Marketing View Groups'),
        default=list,
        blank=True,
        help_text='Gruppen mit Leserechten (z.B. ["Orga","Manager"])'
    )
    marketing_edit_groups = models.JSONField(
        _('Marketing Edit Groups'),
        default=list,
        blank=True,
        help_text='Gruppen mit Schreibrechten (z.B. ["Manager"])'
    )
    marketing_approve_groups = models.JSONField(
        _('Marketing Approve Groups'),
        default=list,
        blank=True,
        help_text='Gruppen mit Freigaberechten (z.B. ["Orga","Manager"])'
    )

    # ERP Permissions (group-based)
    erp_view_groups = models.JSONField(
        _('ERP View Groups'),
        default=list,
        blank=True,
        help_text='Gruppen mit Leserechten (z.B. ["Orga","Manager"])'
    )
    erp_edit_groups = models.JSONField(
        _('ERP Edit Groups'),
        default=list,
        blank=True,
        help_text='Gruppen mit Schreibrechten (z.B. ["Manager"])'
    )
    erp_min_margin_pct = models.DecimalField(
        _('ERP Mindestmarge %'),
        max_digits=6,
        decimal_places=2,
        default=20,
        help_text='Mindestaufschlag in Prozent'
    )
    erp_undercut_min_pct = models.DecimalField(
        _('ERP Unterbieten Min %'),
        max_digits=6,
        decimal_places=2,
        default=3,
        help_text='Minimaler Unterbietungsabstand in Prozent'
    )
    erp_undercut_max_pct = models.DecimalField(
        _('ERP Unterbieten Max %'),
        max_digits=6,
        decimal_places=2,
        default=10,
        help_text='Maximaler Unterbietungsabstand in Prozent'
    )
    erp_competitor_scrape_enabled = models.BooleanField(
        _('ERP Konkurrenz-Scraper aktiv'),
        default=False
    )
    erp_competitor_provider = models.CharField(
        _('ERP Konkurrenz-Provider'),
        max_length=50,
        blank=True,
        default=''
    )
    erp_competitor_api_url = models.URLField(
        _('ERP Konkurrenz API URL'),
        blank=True,
        default=''
    )
    erp_competitor_api_key = models.CharField(
        _('ERP Konkurrenz API Key'),
        max_length=200,
        blank=True,
        default=''
    )
    erp_competitor_accept_terms = models.BooleanField(
        _('ERP Konkurrenz-Provider TOS bestaetigt'),
        default=False
    )

    # Bedrock Settings
    bedrock_enabled = models.BooleanField(
        _('Bedrock aktiviert'),
        default=False,
        help_text='Amazon Bedrock für KI-Funktionen aktivieren'
    )
    bedrock_api_key = models.CharField(
        _('Bedrock API Key'),
        max_length=255,
        blank=True,
        help_text='Bearer Token für Bedrock API'
    )
    bedrock_region = models.CharField(
        _('Bedrock Region'),
        max_length=50,
        default='eu-central-1'
    )
    bedrock_model_id = models.CharField(
        _('Bedrock Model ID'),
        max_length=200,
        default='anthropic.claude-3-5-sonnet-20240620-v1:0'
    )
    bedrock_max_tokens = models.IntegerField(
        _('Bedrock Max Tokens'),
        default=600
    )
    bedrock_temperature = models.FloatField(
        _('Bedrock Temperature'),
        default=0.2
    )

    class Meta:
        verbose_name = _('System Settings')
        verbose_name_plural = _('System Settings')

    def __str__(self):
        return 'System Settings'

    @classmethod
    def get_settings(cls):
        """Get or create default settings"""
        settings_obj, created = cls.objects.get_or_create(id=1)
        return settings_obj

    def get_stats_permissions(self):
        """Get parsed statistics permissions"""
        if isinstance(self.stats_permissions, dict):
            return self.stats_permissions
        try:
            return json.loads(self.stats_permissions) if isinstance(self.stats_permissions, str) else {}
        except:
            return {}

    def set_stats_permissions(self, permissions_dict):
        """Set statistics permissions"""
        self.stats_permissions = permissions_dict

    def get_allowed_extensions(self):
        """Get allowed file extensions"""
        if isinstance(self.allowed_file_types, list):
            return self.allowed_file_types
        try:
            return json.loads(self.allowed_file_types) if isinstance(self.allowed_file_types, str) else []
        except:
            return []

    # ===============================================================
    # LICENSE METHODS - Automatic detection from license code
    # ===============================================================
    
    def get_license_info(self):
        """Get current license information automatically from license code"""
        if not self.license_code:
            return {
                'product': 'TRIAL',
                'product_name': 'Free Trial',
                'valid': True,
                'max_agents': 5,
                'features': ['tickets', 'email', 'knowledge_base'],
                'expiry_date': None,
                'days_remaining': 30,
                'message': 'Trial Mode - 30 days'
            }
        
        license_info = LicenseManager.get_license_info(self.license_code)
        if license_info:
            return license_info
        else:
            return {
                'product': 'INVALID',
                'product_name': 'Invalid License',
                'valid': False,
                'max_agents': 0,
                'features': [],
                'expiry_date': None,
                'days_remaining': 0,
                'message': 'Invalid license code'
            }
    
    def get_license_product(self):
        """Get license product code"""
        return self.get_license_info()['product']
    
    def get_license_product_name(self):
        """Get license product display name"""
        return self.get_license_info()['product_name']
    
    def get_license_max_agents(self):
        """Get maximum agents allowed by license"""
        return self.get_license_info()['max_agents']
    
    def get_license_features(self):
        """Get features enabled by license"""
        return self.get_license_info()['features']
    
    def is_license_valid(self):
        """Check if current license is valid"""
        return self.get_license_info()['valid']
    
    def get_license_expiry_date(self):
        """Get license expiry date"""
        return self.get_license_info().get('expiry_date')
    
    def get_license_days_remaining(self):
        """Get days remaining on license"""
        return self.get_license_info().get('days_remaining', 0)
    
    def has_feature(self, feature_name):
        """Check if specific feature is enabled by license"""
        return feature_name in self.get_license_features()
    
    def can_add_agent(self):
        """Check if more agents can be added based on license"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        current_agents = User.objects.filter(
            role__in=['support_agent', 'admin'],
            is_active=True
        ).count()
        
        max_agents = self.get_license_max_agents()
        return current_agents < max_agents
    
    def get_agent_usage(self):
        """Get current agent usage vs license limit"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        current_agents = User.objects.filter(
            role__in=['support_agent', 'admin'],
            is_active=True
        ).count()
        
        max_agents = self.get_license_max_agents()
        
        return {
            'current': current_agents,
            'max': max_agents,
            'remaining': max(0, max_agents - current_agents),
            'percentage': round((current_agents / max_agents) * 100, 1) if max_agents > 0 else 0
        }


class AuditLog(models.Model):
    """Audit log for settings changes"""

    ACTION_CHOICES = [
        ('created', _('Created')),
        ('updated', _('Updated')),
        ('deleted', _('Deleted')),
        ('email_sent', _('Email Sent')),
        ('file_uploaded', _('File Uploaded')),
    ]

    action = models.CharField(_('Action'), max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='helpdesk_audit_logs',
    )
    content_type = models.CharField(_('Content Type'), max_length=255)
    object_id = models.IntegerField(_('Object ID'), null=True, blank=True)
    description = models.TextField(_('Description'))
    old_values = models.JSONField(_('Old Values'), default=dict, blank=True)
    new_values = models.JSONField(_('New Values'), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), default=timezone_now, db_index=True)

    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.action} - {self.created_at}"


class EmailLog(models.Model):
    subject = models.CharField(max_length=255, blank=True)
    from_email = models.CharField(max_length=255, blank=True)
    to_emails = models.TextField(blank=True)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100, blank=True, default='system')
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.subject}"


class CustomField(models.Model):
    """Dynamic custom fields that can be added to models"""
    
    FIELD_TYPES = [
        ('text', _('Text Field')),
        ('textarea', _('Text Area')),
        ('number', _('Number')),
        ('email', _('Email')),
        ('url', _('URL')),
        ('date', _('Date')),
        ('datetime', _('Date & Time')),
        ('boolean', _('Yes/No')),
        ('select', _('Dropdown')),
        ('multiselect', _('Multiple Selection')),
    ]
    
    TARGET_MODELS = [
        ('user', _('User/Customer')),
        ('ticket', _('Ticket')),
        ('company', _('Company/Organization')),
    ]
    
    name = models.CharField(_('Field Name'), max_length=100)
    label = models.CharField(_('Display Label'), max_length=200)
    field_type = models.CharField(_('Field Type'), max_length=20, choices=FIELD_TYPES)
    target_model = models.CharField(_('Target Model'), max_length=20, choices=TARGET_MODELS)
    
    # Field configuration
    is_required = models.BooleanField(_('Required'), default=False)
    default_value = models.TextField(_('Default Value'), blank=True, null=True)
    help_text = models.TextField(_('Help Text'), blank=True, null=True)
    choices = models.TextField(_('Choices (one per line)'), blank=True, null=True,
                              help_text='For dropdown/multiselect fields, enter one option per line')
    
    # Display options
    is_visible_in_list = models.BooleanField(_('Visible in List View'), default=False)
    is_searchable = models.BooleanField(_('Searchable'), default=False)
    display_order = models.IntegerField(_('Display Order'), default=0)
    
    # Permissions
    visible_to_customers = models.BooleanField(_('Visible to Customers'), default=True)
    editable_by_customers = models.BooleanField(_('Editable by Customers'), default=True)
    
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('created at'), default=timezone_now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Custom Field')
        verbose_name_plural = _('Custom Fields')
        ordering = ['target_model', 'display_order', 'name']
        unique_together = ['name', 'target_model']
    
    def __str__(self):
        return f"{self.get_target_model_display()}: {self.label}"
    
    def get_choices_list(self):
        """Get choices as a list"""
        if self.choices:
            return [choice.strip() for choice in self.choices.split('\n') if choice.strip()]
        return []
    
    def get_form_field(self):
        """Generate Django form field for this custom field"""
        from django import forms
        
        field_kwargs = {
            'label': self.label,
            'required': self.is_required,
            'help_text': self.help_text,
        }
        
        if self.default_value:
            field_kwargs['initial'] = self.default_value
        
        if self.field_type == 'text':
            return forms.CharField(max_length=255, **field_kwargs)
        elif self.field_type == 'textarea':
            return forms.CharField(widget=forms.Textarea, **field_kwargs)
        elif self.field_type == 'number':
            return forms.IntegerField(**field_kwargs)
        elif self.field_type == 'email':
            return forms.EmailField(**field_kwargs)
        elif self.field_type == 'url':
            return forms.URLField(**field_kwargs)
        elif self.field_type == 'date':
            return forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), **field_kwargs)
        elif self.field_type == 'datetime':
            return forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), **field_kwargs)
        elif self.field_type == 'boolean':
            return forms.BooleanField(**field_kwargs)
        elif self.field_type == 'select':
            choices = [(choice, choice) for choice in self.get_choices_list()]
            return forms.ChoiceField(choices=choices, **field_kwargs)
        elif self.field_type == 'multiselect':
            choices = [(choice, choice) for choice in self.get_choices_list()]
            return forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple, **field_kwargs)
        
        return forms.CharField(**field_kwargs)


class CustomFieldValue(models.Model):
    """Values for custom fields"""
    
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name='values')
    object_id = models.PositiveIntegerField(_('Object ID'))  # ID of the target object (user, ticket, etc.)
    value = models.TextField(_('Value'), blank=True, null=True)
    
    created_at = models.DateTimeField(_('created at'), default=timezone_now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Custom Field Value')
        verbose_name_plural = _('Custom Field Values')
        unique_together = ['field', 'object_id']
    
    def __str__(self):
        return f"{self.field.label}: {self.value}"
    
    def get_formatted_value(self):
        """Get value formatted according to field type"""
        if not self.value:
            return None
        
        if self.field.field_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes', 'on']
        elif self.field.field_type == 'number':
            try:
                return int(self.value)
            except ValueError:
                return None
        elif self.field.field_type == 'multiselect':
            try:
                return json.loads(self.value) if self.value.startswith('[') else [self.value]
            except (json.JSONDecodeError, AttributeError):
                return [self.value]
        
        return self.value
