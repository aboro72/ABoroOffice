from django import forms
from .models import Account, CostCenter, CostType, BusinessPartner, JournalEntry, JournalLine, FibuSettings


class BaseFibuForm(forms.ModelForm):
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


class AccountForm(BaseFibuForm):
    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type', 'is_active']


class CostCenterForm(BaseFibuForm):
    class Meta:
        model = CostCenter
        fields = ['code', 'name', 'cost_center_type', 'account', 'description', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class CostTypeForm(BaseFibuForm):
    class Meta:
        model = CostType
        fields = ['code', 'name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class BusinessPartnerForm(BaseFibuForm):
    class Meta:
        model = BusinessPartner
        fields = ['partner_type', 'partner_number', 'name', 'vat_id', 'address']
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}


class JournalEntryForm(BaseFibuForm):
    class Meta:
        model = JournalEntry
        fields = [
            'date',
            'reference',
            'description',
            'erp_invoice',
            'erp_salesorder',
            'erp_stockreceipt',
            'contract',
            'employee',
        ]
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}


class JournalLineForm(BaseFibuForm):
    class Meta:
        model = JournalLine
        fields = ['account', 'cost_center', 'cost_type', 'partner', 'debit', 'credit', 'description']


class FibuSettingsForm(BaseFibuForm):
    class Meta:
        model = FibuSettings
        fields = [
            'auto_posting_enabled',
            'receivable_account',
            'revenue_account',
            'vat_output_account',
            'inventory_account',
            'payable_account',
            'expense_account',
            'default_cost_center',
        ]


class AccountImportForm(forms.Form):
    file = forms.FileField()
