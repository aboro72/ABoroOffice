from django import forms
from .models import Campaign, ContentAsset, ContentIdea, ContentApproval


class BaseMarketingForm(forms.ModelForm):
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


class CampaignForm(BaseMarketingForm):
    class Meta:
        model = Campaign
        fields = [
            'name',
            'objective',
            'status',
            'start_date',
            'end_date',
            'owner',
            'kpi_impressions',
            'kpi_clicks',
            'kpi_conversions',
            'kpi_spend',
            'kpi_revenue',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ContentAssetForm(BaseMarketingForm):
    class Meta:
        model = ContentAsset
        fields = ['title', 'asset_type', 'channel', 'campaign', 'brief', 'content', 'status', 'scheduled_at']
        widgets = {
            'brief': forms.Textarea(attrs={'rows': 4}),
            'content': forms.Textarea(attrs={'rows': 10}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ContentIdeaForm(BaseMarketingForm):
    class Meta:
        model = ContentIdea
        fields = ['title', 'description', 'target_audience']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ApprovalForm(BaseMarketingForm):
    class Meta:
        model = ContentApproval
        fields = ['status', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }
