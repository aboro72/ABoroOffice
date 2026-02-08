from django import forms
from .models import Contract, ContractVersion


class BaseContractForm(forms.ModelForm):
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


class ContractForm(BaseContractForm):
    class Meta:
        model = Contract
        fields = [
            'title',
            'counterparty',
            'status',
            'start_date',
            'end_date',
            'renewal_date',
            'value_eur',
            'owner',
            'file',
            'notes',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'renewal_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ContractVersionForm(BaseContractForm):
    class Meta:
        model = ContractVersion
        fields = [
            'contract',
            'label',
            'file',
            'summary',
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
        }
