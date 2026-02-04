from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
from apps.helpdesk.helpdesk_apps.chat.models import ChatSettings


class AdminSettingsForm(forms.Form):
    """Combined form for System Settings and Chat Settings"""
    
    # System Settings - Branding
    app_name = forms.CharField(
        label='Anwendungsname',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    company_name = forms.CharField(
        label='Firmenname',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    logo = forms.ImageField(
        label='Logo',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    site_url = forms.URLField(
        label='Website URL',
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    
    # System Settings - SMTP (Outgoing)
    smtp_host = forms.CharField(
        label='SMTP Server',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    smtp_port = forms.IntegerField(
        label='SMTP Port',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    smtp_username = forms.CharField(
        label='SMTP Benutzername',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    smtp_password = forms.CharField(
        label='SMTP Passwort',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leer lassen, um beizubehalten'})
    )
    smtp_use_tls = forms.BooleanField(
        label='TLS verwenden',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # System Settings - IMAP (Incoming)
    imap_enabled = forms.BooleanField(
        label='IMAP aktivieren (E-Mails automatisch zu Tickets)',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    imap_host = forms.CharField(
        label='IMAP Server',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. mail.aboro-it.net'})
    )
    imap_port = forms.IntegerField(
        label='IMAP Port',
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '993'})
    )
    imap_username = forms.CharField(
        label='IMAP Benutzername',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    imap_password = forms.CharField(
        label='IMAP Passwort',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leer lassen, um beizubehalten'})
    )
    imap_use_ssl = forms.BooleanField(
        label='SSL verwenden',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    imap_folder = forms.CharField(
        label='IMAP Ordner',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. INBOX'})
    )
    
    # System Settings - Features
    send_email_notifications = forms.BooleanField(
        label='E-Mail Benachrichtigungen senden',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    max_upload_size_mb = forms.IntegerField(
        label='Maximale Upload-Größe (MB)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Chat Settings
    chat_enabled = forms.BooleanField(
        label='Live Chat aktiviert',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    widget_color = forms.CharField(
        label='Chat Widget Farbe',
        max_length=7,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'})
    )
    widget_position = forms.ChoiceField(
        label='Chat Widget Position',
        choices=[('bottom-right', 'Unten Rechts'), ('bottom-left', 'Unten Links')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    welcome_message = forms.CharField(
        label='Willkommensnachricht',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    offline_message = forms.CharField(
        label='Offline-Nachricht',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    auto_assign = forms.BooleanField(
        label='Automatische Zuweisung',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # AI Settings
    ai_enabled = forms.BooleanField(
        label='KI Chat Support aktiviert',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    ai_provider = forms.ChoiceField(
        label='KI Provider',
        choices=[
            ('llama3', 'LLAMA3 (Lokal - kostenlos)'),
            ('chatgpt', 'ChatGPT (OpenAI)'),
            ('claude', 'Claude (Anthropic)')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    openai_api_key = forms.CharField(
        label='OpenAI API Key',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'sk-...'})
    )
    anthropic_api_key = forms.CharField(
        label='Anthropic API Key',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'sk-ant-...'})
    )
    ai_response_delay = forms.IntegerField(
        label='KI Antwort Verzögerung (Sekunden)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '60'})
    )
    ai_max_tokens = forms.IntegerField(
        label='KI Max Tokens',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '100', 'max': '2000'})
    )

    # Theme Settings
    theme_variant = forms.ChoiceField(
        label='Design Theme',
        choices=[
            ('default', 'Default (Modern Blue)'),
            ('professional', 'Professional (Dark Blue)'),
            ('bright', 'Bright (Orange)'),
            ('modern', 'Modern (Indigo & Teal)'),
            ('corporate', 'Corporate (Navy Blue)'),
            ('dark', 'Dark Mode (Dark Gray & Blue)'),
            ('custom', 'Custom (Eigenes Design)'),
        ],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_theme_variant'})
    )
    primary_color = forms.CharField(
        label='Primärfarbe',
        max_length=7,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'})
    )
    secondary_color = forms.CharField(
        label='Sekundärfarbe',
        max_length=7,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'})
    )
    accent_color = forms.CharField(
        label='Akzentfarbe',
        max_length=7,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'})
    )
    danger_color = forms.CharField(
        label='Warnfarbe',
        max_length=7,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'})
    )
    font_family = forms.ChoiceField(
        label='Schriftart',
        choices=[
            ('inter', 'Inter (Modern)'),
            ('roboto', 'Roboto (Standard)'),
            ('playfair', 'Playfair (Elegant)'),
            ('poppins', 'Poppins (Casual)'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    border_radius = forms.IntegerField(
        label='Eckenradius (px)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '20'})
    )
    enable_dark_mode = forms.BooleanField(
        label='Dark Mode Umschalter aktivieren',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.system_settings = kwargs.pop('system_settings', None)
        self.chat_settings = kwargs.pop('chat_settings', None)
        super().__init__(*args, **kwargs)
        
        # Populate form with current values
        if self.system_settings:
            self.fields['app_name'].initial = self.system_settings.app_name
            self.fields['company_name'].initial = self.system_settings.company_name
            self.fields['site_url'].initial = self.system_settings.site_url
            # SMTP
            self.fields['smtp_host'].initial = self.system_settings.smtp_host
            self.fields['smtp_port'].initial = self.system_settings.smtp_port
            self.fields['smtp_username'].initial = self.system_settings.smtp_username
            self.fields['smtp_password'].initial = self.system_settings.smtp_password
            self.fields['smtp_use_tls'].initial = self.system_settings.smtp_use_tls
            # IMAP
            self.fields['imap_enabled'].initial = self.system_settings.imap_enabled
            self.fields['imap_host'].initial = self.system_settings.imap_host
            self.fields['imap_port'].initial = self.system_settings.imap_port
            self.fields['imap_username'].initial = self.system_settings.imap_username
            self.fields['imap_password'].initial = self.system_settings.imap_password
            self.fields['imap_use_ssl'].initial = self.system_settings.imap_use_ssl
            self.fields['imap_folder'].initial = self.system_settings.imap_folder
            # Features
            self.fields['send_email_notifications'].initial = self.system_settings.send_email_notifications
            self.fields['max_upload_size_mb'].initial = self.system_settings.max_upload_size_mb
            # AI Settings
            self.fields['ai_enabled'].initial = self.system_settings.ai_enabled
            self.fields['ai_provider'].initial = self.system_settings.ai_provider
            self.fields['openai_api_key'].initial = self.system_settings.openai_api_key
            self.fields['anthropic_api_key'].initial = self.system_settings.anthropic_api_key
            self.fields['ai_response_delay'].initial = self.system_settings.ai_response_delay
            self.fields['ai_max_tokens'].initial = self.system_settings.ai_max_tokens
            # Theme Settings
            self.fields['theme_variant'].initial = self.system_settings.theme_variant
            self.fields['primary_color'].initial = self.system_settings.primary_color
            self.fields['secondary_color'].initial = self.system_settings.secondary_color
            self.fields['accent_color'].initial = self.system_settings.accent_color
            self.fields['danger_color'].initial = self.system_settings.danger_color
            self.fields['font_family'].initial = self.system_settings.font_family
            self.fields['border_radius'].initial = self.system_settings.border_radius
            self.fields['enable_dark_mode'].initial = self.system_settings.enable_dark_mode
        
        if self.chat_settings:
            self.fields['chat_enabled'].initial = self.chat_settings.is_enabled
            self.fields['widget_color'].initial = self.chat_settings.widget_color
            self.fields['widget_position'].initial = self.chat_settings.widget_position
            self.fields['welcome_message'].initial = self.chat_settings.welcome_message
            self.fields['offline_message'].initial = self.chat_settings.offline_message
            self.fields['auto_assign'].initial = self.chat_settings.auto_assign
    
    def save(self):
        """Save both system and chat settings"""
        if self.system_settings:
            # Update system settings
            self.system_settings.app_name = self.cleaned_data['app_name']
            self.system_settings.company_name = self.cleaned_data['company_name']
            self.system_settings.site_url = self.cleaned_data['site_url']

            # SMTP settings
            self.system_settings.smtp_host = self.cleaned_data['smtp_host']
            self.system_settings.smtp_port = self.cleaned_data['smtp_port']
            self.system_settings.smtp_username = self.cleaned_data['smtp_username']
            if self.cleaned_data['smtp_password']:  # Only update password if provided
                self.system_settings.smtp_password = self.cleaned_data['smtp_password']
            self.system_settings.smtp_use_tls = self.cleaned_data['smtp_use_tls']

            # IMAP settings
            self.system_settings.imap_enabled = self.cleaned_data['imap_enabled']
            if self.cleaned_data['imap_host']:
                self.system_settings.imap_host = self.cleaned_data['imap_host']
            if self.cleaned_data['imap_port']:
                self.system_settings.imap_port = self.cleaned_data['imap_port']
            if self.cleaned_data['imap_username']:
                self.system_settings.imap_username = self.cleaned_data['imap_username']
            if self.cleaned_data['imap_password']:  # Only update password if provided
                self.system_settings.imap_password = self.cleaned_data['imap_password']
            self.system_settings.imap_use_ssl = self.cleaned_data['imap_use_ssl']
            if self.cleaned_data['imap_folder']:
                self.system_settings.imap_folder = self.cleaned_data['imap_folder']

            # Other settings
            self.system_settings.send_email_notifications = self.cleaned_data['send_email_notifications']
            self.system_settings.max_upload_size_mb = self.cleaned_data['max_upload_size_mb']

            # AI Settings
            self.system_settings.ai_enabled = self.cleaned_data['ai_enabled']
            self.system_settings.ai_provider = self.cleaned_data['ai_provider']
            if self.cleaned_data['openai_api_key']:
                self.system_settings.openai_api_key = self.cleaned_data['openai_api_key']
            if self.cleaned_data['anthropic_api_key']:
                self.system_settings.anthropic_api_key = self.cleaned_data['anthropic_api_key']
            self.system_settings.ai_response_delay = self.cleaned_data['ai_response_delay']
            self.system_settings.ai_max_tokens = self.cleaned_data['ai_max_tokens']

            # Theme Settings
            self.system_settings.theme_variant = self.cleaned_data['theme_variant']
            self.system_settings.primary_color = self.cleaned_data['primary_color']
            self.system_settings.secondary_color = self.cleaned_data['secondary_color']
            self.system_settings.accent_color = self.cleaned_data['accent_color']
            self.system_settings.danger_color = self.cleaned_data['danger_color']
            self.system_settings.font_family = self.cleaned_data['font_family']
            self.system_settings.border_radius = self.cleaned_data['border_radius']
            self.system_settings.enable_dark_mode = self.cleaned_data['enable_dark_mode']

            # Handle logo upload
            if 'logo' in self.files:
                self.system_settings.logo = self.files['logo']

            self.system_settings.save()

        if self.chat_settings:
            # Update chat settings
            self.chat_settings.is_enabled = self.cleaned_data['chat_enabled']
            self.chat_settings.widget_color = self.cleaned_data['widget_color']
            self.chat_settings.widget_position = self.cleaned_data['widget_position']
            self.chat_settings.welcome_message = self.cleaned_data['welcome_message']
            self.chat_settings.offline_message = self.cleaned_data['offline_message']
            self.chat_settings.auto_assign = self.cleaned_data['auto_assign']
            self.chat_settings.save()