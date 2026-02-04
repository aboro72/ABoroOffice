from django import forms
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


APP_TOGGLE_FIELDS = [
    ('approvals', 'SSH Approvals'),
    ('helpdesk', 'Helpdesk'),
    ('cloudstorage', 'CloudStorage'),
    ('classroom', 'Classroom'),
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
            'logo',
            'site_url',
        ]
        widgets = {
            'app_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'site_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class AppTogglesForm(forms.Form):
    """Toggle access to apps globally."""

    approvals = forms.BooleanField(label='SSH Approvals', required=False)
    helpdesk = forms.BooleanField(label='Helpdesk', required=False)
    cloudstorage = forms.BooleanField(label='CloudStorage', required=False)
    classroom = forms.BooleanField(label='Classroom', required=False)

    def __init__(self, *args, **kwargs):
        settings_obj = kwargs.pop('system_settings', None)
        super().__init__(*args, **kwargs)
        if settings_obj:
            toggles = settings_obj.app_toggles or {}
            self.fields['approvals'].initial = toggles.get('approvals', False)
            self.fields['helpdesk'].initial = toggles.get('helpdesk', True)
            self.fields['cloudstorage'].initial = toggles.get('cloudstorage', True)
            self.fields['classroom'].initial = toggles.get('classroom', True)
