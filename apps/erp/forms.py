from django import forms
from .models import (
    Customer,
    Product,
    Service,
    ProductCategory,
    WorkOrder,
    SalesOrder,
    SalesOrderItem,
    Quote,
    QuoteItem,
    OrderConfirmation,
    DunningNotice,
    StockReceipt,
    StockReceiptItem,
    Course,
)
from apps.personnel.models import Instructor


class BaseErpForm(forms.ModelForm):
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


class CustomerForm(BaseErpForm):
    class Meta:
        model = Customer
        fields = ['name', 'customer_type', 'email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class ProductForm(BaseErpForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'sku',
            'categories',
            'image',
            'price',
            'cost_net',
            'vat_rate',
            'stock_qty',
            'reorder_level',
            'competitor_price_net',
            'suggested_price_net',
            'suggested_price_gross',
            'description',
            'marketing_campaign',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ServiceForm(BaseErpForm):
    class Meta:
        model = Service
        fields = ['name', 'categories', 'image', 'hourly_rate', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProductCategoryForm(BaseErpForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'parent', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class WorkOrderForm(BaseErpForm):
    class Meta:
        model = WorkOrder
        fields = ['customer', 'title', 'description', 'status', 'scheduled_for', 'assigned_to', 'contract']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'scheduled_for': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class SalesOrderForm(BaseErpForm):
    class Meta:
        model = SalesOrder
        fields = ['customer', 'status', 'tax_rate', 'contract']


class SalesOrderItemForm(BaseErpForm):
    class Meta:
        model = SalesOrderItem
        fields = ['product', 'quantity', 'unit_price']


class QuoteForm(BaseErpForm):
    class Meta:
        model = Quote
        fields = ['customer', 'status', 'issue_date', 'valid_until', 'tax_rate', 'notes']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class QuoteItemForm(BaseErpForm):
    class Meta:
        model = QuoteItem
        fields = ['product', 'description', 'quantity', 'unit_price']


class OrderConfirmationForm(BaseErpForm):
    class Meta:
        model = OrderConfirmation
        fields = ['order', 'status']


class DunningNoticeForm(BaseErpForm):
    class Meta:
        model = DunningNotice
        fields = ['invoice', 'level', 'status', 'due_date', 'email_subject', 'email_body', 'letter_text']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'email_body': forms.Textarea(attrs={'rows': 5}),
            'letter_text': forms.Textarea(attrs={'rows': 6}),
        }


class StockReceiptForm(BaseErpForm):
    class Meta:
        model = StockReceipt
        fields = ['supplier_name', 'receipt_date', 'invoice_file', 'notes']
        widgets = {
            'receipt_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class StockReceiptItemForm(BaseErpForm):
    class Meta:
        model = StockReceiptItem
        fields = ['product', 'quantity', 'unit_cost_net', 'competitor_price_net']


class CourseForm(BaseErpForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'event_number' in self.fields:
            self.fields['event_number'].widget.attrs['readonly'] = True
        if 'instructor' in self.fields and 'required_skill' in self.fields:
            skill_id = None
            if self.data.get('required_skill'):
                skill_id = self.data.get('required_skill')
            elif self.instance and self.instance.required_skill_id:
                skill_id = self.instance.required_skill_id
            if skill_id:
                self.fields['instructor'].queryset = Instructor.objects.filter(skills__id=skill_id).order_by('name')
            else:
                self.fields['instructor'].queryset = Instructor.objects.all().order_by('name')

    class Meta:
        model = Course
        fields = [
            'event_number',
            'title',
            'customer',
            'required_skill',
            'instructor',
            'work_order',
            'contract',
            'status',
            'instructor_days',
            'instructor_daily_cost',
            'expenses',
            'lodging',
            'mobile_classroom_required',
            'mobile_classroom_product',
            'mobile_classroom_cost',
            'vat_rate',
            'start_date',
            'end_date',
            'capacity',
            'description',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
