from django import forms
from .models import Account, Lead, Opportunity, EmailTemplate, LeadSourceProfile, LeadStaging, Note, Activity


class BaseCrmForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')
            else:
                widget.attrs.setdefault('class', 'form-control')


class AccountForm(BaseCrmForm):
    class Meta:
        model = Account
        fields = [
            'name',
            'industry',
            'website',
            'phone',
            'email',
            'address',
            'status',
            'owner',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class LeadForm(BaseCrmForm):
    class Meta:
        model = Lead
        fields = [
            'name',
            'company',
            'email',
            'phone',
            'website',
            'address',
            'source',
            'status',
            'owner',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }


class OpportunityForm(BaseCrmForm):
    class Meta:
        model = Opportunity
        fields = [
            'account',
            'name',
            'stage',
            'amount',
            'close_date',
            'owner',
        ]
        widgets = {
            'close_date': forms.DateInput(attrs={'type': 'date'}),
        }


class EmailTemplateForm(BaseCrmForm):
    class Meta:
        model = EmailTemplate
        fields = [
            'name',
            'slug',
            'description',
            'subject',
            'body',
            'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'body': forms.Textarea(attrs={'rows': 8}),
        }


class EmailSendForm(forms.Form):
    template = forms.ModelChoiceField(queryset=EmailTemplate.objects.none())
    to_email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['template'].queryset = EmailTemplate.objects.filter(is_active=True)
        self.fields['template'].widget.attrs.setdefault('class', 'form-select')
        self.fields['to_email'].widget.attrs.setdefault('class', 'form-control')


class LeadSourceProfileForm(BaseCrmForm):
    class Meta:
        model = LeadSourceProfile
        fields = [
            'name',
            'source',
            'keywords',
            'keyword_mode',
            'search_type',
            'results_per_page',
            'register_art',
            'register_nummer',
            'register_gericht',
            'rechtsform',
            'ort',
            'postleitzahl',
            'strasse',
            'niederlassung',
            'bundesland_bw',
            'bundesland_by',
            'bundesland_be',
            'bundesland_br',
            'bundesland_hb',
            'bundesland_hh',
            'bundesland_he',
            'bundesland_mv',
            'bundesland_ni',
            'bundesland_nw',
            'bundesland_rp',
            'bundesland_sl',
            'bundesland_sn',
            'bundesland_st',
            'bundesland_sh',
            'bundesland_th',
            'suchoptionen_aehnlich',
            'suchoptionen_geloescht',
            'suchoptionen_nur_zn_neuen_rechts',
            'enabled',
            'schedule',
            'max_per_run',
        ]


class LeadStagingForm(BaseCrmForm):
    website = forms.URLField(label='Website', required=False)
    address = forms.CharField(
        label='Adresse',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        help_text='Vollständige Anschrift'
    )

    class Meta:
        model = LeadStaging
        fields = [
            'name',
            'company',
            'email',
            'phone',
            'source',
            'status',
            'lead_source',
            'lead_status',
            'enrichment_status',
            'enrichment_notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raw = {}
        if self.instance and isinstance(self.instance.raw_data, dict):
            raw = self.instance.raw_data
        website = raw.get('website') or raw.get('source_url') or ''
        address = raw.get('address') or ''
        if not address:
            street = raw.get('strasse') or raw.get('street') or ''
            zip_code = raw.get('postleitzahl') or raw.get('zip') or ''
            city = raw.get('ort') or raw.get('city') or ''
            country = raw.get('land') or raw.get('country') or ''
            parts = [p for p in [street, " ".join([zip_code, city]).strip(), country] if p]
            address = ", ".join(parts)
        self.fields['website'].initial = website
        self.fields['address'].initial = address
        self.order_fields([
            'name',
            'company',
            'email',
            'website',
            'address',
            'phone',
            'source',
            'status',
            'lead_source',
            'lead_status',
            'enrichment_status',
            'enrichment_notes',
        ])

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = instance.raw_data if isinstance(instance.raw_data, dict) else {}
        website = self.cleaned_data.get('website') or ''
        address = self.cleaned_data.get('address') or ''
        if website:
            raw['website'] = website
        if address:
            raw['address'] = address
        instance.raw_data = raw
        if commit:
            instance.save()
        return instance


class NoteForm(BaseCrmForm):
    class Meta:
        model = Note
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Notiz hinzufügen...'}),
        }


class ActivityForm(BaseCrmForm):
    class Meta:
        model = Activity
        fields = ['activity_type', 'subject', 'due_date', 'status']
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': 'z.B. Rückruf vereinbaren'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
