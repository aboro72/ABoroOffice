from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView
from django.urls import reverse
from django.contrib import messages
from django.db import models
from django.utils import timezone
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
from apps.cloude.cloude_apps.plugins.models import Plugin
from .permissions import ErpViewMixin, ErpEditMixin, can_edit_erp
from .models import (
    Customer,
    Product,
    Service,
    WorkOrder,
    SalesOrder,
    SalesOrderItem,
    Invoice,
    Quote,
    QuoteItem,
    OrderConfirmation,
    DunningNotice,
    StockReceipt,
    StockReceiptItem,
    Course,
)
from .forms import (
    CustomerForm,
    ProductForm,
    ServiceForm,
    WorkOrderForm,
    SalesOrderForm,
    SalesOrderItemForm,
    QuoteForm,
    QuoteItemForm,
    DunningNoticeForm,
    StockReceiptForm,
    StockReceiptItemForm,
    CourseForm,
)
from .services.invoicing import create_invoice_for_order
from .services.quotes import create_order_from_quote
from .services.dunning import build_letter_text, send_dunning_email, mark_sent
from .services.dunning_auto import run_dunning_cycle
from .services.invoice_mail import build_invoice_letter, send_invoice_email
from .services.pdf import build_letter_pdf, build_invoice_pdf, build_dunning_pdf
from .services.pricing import apply_pricing
from .services.competitor import get_provider
from django.core.cache import cache


class ErpHomeView(ErpViewMixin, TemplateView):
    template_name = 'erp/home.html'


class CustomerListView(ErpViewMixin, ListView):
    model = Customer
    template_name = 'erp/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 25

    def get_queryset(self):
        qs = Customer.objects.all()
        q = self.request.GET.get('q')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if q:
            qs = qs.filter(models.Q(name__icontains=q) | models.Q(email__icontains=q))
        allowed_sorts = {'name', '-name', 'created_at', '-created_at'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class CustomerCreateView(ErpEditMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Kunde erstellen'
        return context

    def get_success_url(self):
        return reverse('erp:customers')


class CustomerUpdateView(ErpEditMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Kunde bearbeiten'
        return context

    def get_success_url(self):
        return reverse('erp:customers')


class ProductListView(ErpViewMixin, ListView):
    model = Product
    template_name = 'erp/product_list.html'
    context_object_name = 'products'
    paginate_by = 25

    def get_queryset(self):
        qs = Product.objects.all()
        q = self.request.GET.get('q')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if q:
            qs = qs.filter(models.Q(name__icontains=q) | models.Q(sku__icontains=q))
        allowed_sorts = {'name', '-name', 'created_at', '-created_at', 'sku', '-sku'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
            ('sku', 'SKU A-Z'),
            ('-sku', 'SKU Z-A'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class ProductCreateView(ErpEditMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Produkt erstellen'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        apply_pricing(self.object)
        return response

    def get_success_url(self):
        return reverse('erp:products')


class ProductUpdateView(ErpEditMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Produkt bearbeiten'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        apply_pricing(self.object)
        return response

    def get_success_url(self):
        return reverse('erp:products')


class ServiceListView(ErpViewMixin, ListView):
    model = Service
    template_name = 'erp/service_list.html'
    context_object_name = 'services'
    paginate_by = 25

    def get_queryset(self):
        qs = Service.objects.all()
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        allowed_sorts = {'name', '-name', 'created_at', '-created_at'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class ServiceCreateView(ErpEditMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Service erstellen'
        return context

    def get_success_url(self):
        return reverse('erp:services')


class ServiceUpdateView(ErpEditMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Service bearbeiten'
        return context

    def get_success_url(self):
        return reverse('erp:services')


class WorkOrderListView(ErpViewMixin, ListView):
    model = WorkOrder
    template_name = 'erp/workorder_list.html'
    context_object_name = 'workorders'
    paginate_by = 25

    def get_queryset(self):
        qs = WorkOrder.objects.select_related('customer').all()
        q = self.request.GET.get('q')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if q:
            qs = qs.filter(models.Q(title__icontains=q) | models.Q(customer__name__icontains=q))
        allowed_sorts = {'title', '-title', 'created_at', '-created_at', 'due_date', '-due_date'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('title', 'Titel A-Z'),
            ('-title', 'Titel Z-A'),
            ('-due_date', 'Fällig spaeter'),
            ('due_date', 'Fällig frueher'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class QuoteListView(ErpViewMixin, ListView):
    model = Quote
    template_name = 'erp/quote_list.html'
    context_object_name = 'quotes'
    paginate_by = 25

    def get_queryset(self):
        qs = Quote.objects.select_related('customer').all()
        q = self.request.GET.get('q')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if q:
            qs = qs.filter(models.Q(number__icontains=q) | models.Q(customer__name__icontains=q))
        allowed_sorts = {'number', '-number', 'created_at', '-created_at'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('number', 'Nummer A-Z'),
            ('-number', 'Nummer Z-A'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class QuoteCreateView(ErpEditMixin, CreateView):
    model = Quote
    form_class = QuoteForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Angebot erstellen'
        return context

    def get_success_url(self):
        return reverse('erp:quote_detail', kwargs={'pk': self.object.pk})


class QuoteDetailView(ErpViewMixin, DetailView):
    model = Quote
    template_name = 'erp/quote_detail.html'
    context_object_name = 'quote'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_form'] = QuoteItemForm()
        context['items'] = self.object.items.select_related('product').all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_erp(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return self.get(request, *args, **kwargs)
        if 'add_item' in request.POST:
            form = QuoteItemForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.quote = self.object
                item.save()
                messages.success(request, 'Position hinzugefuegt.')
            else:
                messages.error(request, 'Bitte pruefe die Position.')
            return self.get(request, *args, **kwargs)

        if 'create_order' in request.POST:
            order = create_order_from_quote(self.object)
            messages.success(request, f'Auftrag {order.order_number} erstellt.')
            return self.get(request, *args, **kwargs)

        return self.get(request, *args, **kwargs)


class WorkOrderCreateView(ErpEditMixin, CreateView):
    model = WorkOrder
    form_class = WorkOrderForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Auftrag erstellen'
        return context

    def get_success_url(self):
        return reverse('erp:workorders')


class WorkOrderUpdateView(ErpEditMixin, UpdateView):
    model = WorkOrder
    form_class = WorkOrderForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Auftrag bearbeiten'
        return context

    def get_success_url(self):
        return reverse('erp:workorders')


class SalesOrderListView(ErpViewMixin, ListView):
    model = SalesOrder
    template_name = 'erp/salesorder_list.html'
    context_object_name = 'orders'
    paginate_by = 25

    def get_queryset(self):
        qs = SalesOrder.objects.select_related('customer').all()
        q = self.request.GET.get('q')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if q:
            qs = qs.filter(models.Q(order_number__icontains=q) | models.Q(customer__name__icontains=q))
        allowed_sorts = {'order_number', '-order_number', 'created_at', '-created_at'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('order_number', 'Nummer A-Z'),
            ('-order_number', 'Nummer Z-A'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class SalesOrderCreateView(ErpEditMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Sales Order erstellen'
        return context

    def get_success_url(self):
        return reverse('erp:salesorders')


class SalesOrderDetailView(ErpViewMixin, DetailView):
    model = SalesOrder
    template_name = 'erp/salesorder_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_form'] = SalesOrderItemForm()
        context['items'] = self.object.items.select_related('product').all()
        context['invoices'] = self.object.invoices.all().order_by('-created_at')
        context['confirmations'] = self.object.confirmations.all().order_by('-created_at')
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_erp(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return self.get(request, *args, **kwargs)
        if 'add_item' in request.POST:
            form = SalesOrderItemForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.order = self.object
                item.save()
                messages.success(request, 'Position hinzugefuegt.')
            else:
                messages.error(request, 'Bitte pruefe die Position.')
            return self.get(request, *args, **kwargs)

        if 'create_invoice' in request.POST:
            invoice = create_invoice_for_order(self.object)
            messages.success(request, f'Rechnung {invoice.number} erstellt.')
            return self.get(request, *args, **kwargs)

        return self.get(request, *args, **kwargs)


class SalesOrderUpdateView(ErpEditMixin, UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Sales Order bearbeiten'
        return context

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_locked:
            messages.error(request, 'Auftrag ist gesperrt und kann nicht bearbeitet werden.')
            return redirect('erp:salesorder_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('erp:salesorder_detail', kwargs={'pk': self.object.pk})


class InvoiceListView(ErpViewMixin, ListView):
    model = Invoice
    template_name = 'erp/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 25

    def get_queryset(self):
        qs = Invoice.objects.select_related('order', 'order__customer').all()
        q = self.request.GET.get('q')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if q:
            qs = qs.filter(models.Q(number__icontains=q) | models.Q(order__customer__name__icontains=q))
        allowed_sorts = {'number', '-number', 'created_at', '-created_at'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('number', 'Nummer A-Z'),
            ('-number', 'Nummer Z-A'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class InvoiceDetailView(ErpViewMixin, DetailView):
    model = Invoice
    template_name = 'erp/invoice_detail.html'
    context_object_name = 'invoice'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_erp(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return self.get(request, *args, **kwargs)
        if 'create_dunning' in request.POST:
            notice = DunningNotice.objects.create(
                invoice=self.object,
                level=int(request.POST.get('level', 1)),
                status='draft',
            )
            notice.letter_text = build_letter_text(notice)
            notice.email_subject = f"Mahnung {notice.number}"
            notice.email_body = notice.letter_text
            notice.save(update_fields=['letter_text', 'email_subject', 'email_body'])
            messages.success(request, f'Mahnung {notice.number} erstellt.')
        if 'send_invoice' in request.POST:
            sent = send_invoice_email(self.object)
            if sent:
                self.object.email_sent_at = timezone.now()
                self.object.save(update_fields=['email_sent_at'])
                messages.success(request, 'Rechnung per E-Mail versendet.')
            else:
                messages.error(request, 'E-Mail konnte nicht versendet werden.')
        if 'download_invoice_letter' in request.POST:
            letter = build_invoice_letter(self.object)
            response = HttpResponse(letter, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename=\"{self.object.number}.txt\"'
            return response
        return self.get(request, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_erp(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return self.get(request, *args, **kwargs)
        if 'create_dunning' in request.POST:
            notice = DunningNotice.objects.create(
                invoice=self.object,
                level=int(request.POST.get('level', 1)),
                status='draft',
            )
            notice.letter_text = build_letter_text(notice)
            notice.email_subject = f"Mahnung {notice.number}"
            notice.email_body = notice.letter_text
            notice.save(update_fields=['letter_text', 'email_subject', 'email_body'])
            messages.success(request, f'Mahnung {notice.number} erstellt.')
        return self.get(request, *args, **kwargs)


class OrderConfirmationListView(ErpViewMixin, ListView):
    model = OrderConfirmation
    template_name = 'erp/order_confirmation_list.html'
    context_object_name = 'confirmations'
    paginate_by = 25

    def get_queryset(self):
        qs = OrderConfirmation.objects.select_related('order', 'order__customer').all()
        q = self.request.GET.get('q')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if q:
            qs = qs.filter(models.Q(number__icontains=q) | models.Q(order__customer__name__icontains=q))
        allowed_sorts = {'number', '-number', 'created_at', '-created_at'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('number', 'Nummer A-Z'),
            ('-number', 'Nummer Z-A'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class DunningListView(ErpViewMixin, ListView):
    model = DunningNotice
    template_name = 'erp/dunning_list.html'
    context_object_name = 'notices'
    paginate_by = 25

    def get_queryset(self):
        qs = DunningNotice.objects.select_related('invoice', 'invoice__order__customer').all()
        q = self.request.GET.get('q')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if q:
            qs = qs.filter(models.Q(number__icontains=q) | models.Q(invoice__number__icontains=q))
        allowed_sorts = {'number', '-number', 'created_at', '-created_at', 'level', '-level'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('number', 'Nummer A-Z'),
            ('-number', 'Nummer Z-A'),
            ('-level', 'Stufe hoch'),
            ('level', 'Stufe niedrig'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class DunningDetailView(ErpViewMixin, DetailView):
    model = DunningNotice
    template_name = 'erp/dunning_detail.html'
    context_object_name = 'notice'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_erp(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return self.get(request, *args, **kwargs)
        if 'send_email' in request.POST:
            sent = send_dunning_email(self.object)
            if sent:
                mark_sent(self.object)
                messages.success(request, 'Mahnung per E-Mail versendet.')
            else:
                messages.error(request, 'E-Mail konnte nicht versendet werden.')
        if 'download_letter' in request.POST:
            response = HttpResponse(self.object.letter_text, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename=\"{self.object.number}.txt\"'
            return response
        return self.get(request, *args, **kwargs)


class DunningRunView(ErpViewMixin, TemplateView):
    template_name = 'erp/dunning_run.html'

    def post(self, request, *args, **kwargs):
        if not can_edit_erp(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return redirect('erp:dunning')
        result = run_dunning_cycle()
        messages.success(request, f"Mahnwesen ausgeführt: {result['created']} erstellt, {result['sent']} gesendet.")
        return redirect('erp:dunning')


class StockReceiptListView(ErpViewMixin, ListView):
    model = StockReceipt
    template_name = 'erp/stockreceipt_list.html'
    context_object_name = 'receipts'
    paginate_by = 25

    def get_queryset(self):
        qs = StockReceipt.objects.all()
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        allowed_sorts = {'created_at', '-created_at', 'receipt_date', '-receipt_date'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('-receipt_date', 'Datum spaeter'),
            ('receipt_date', 'Datum frueher'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class StockReceiptCreateView(ErpEditMixin, CreateView):
    model = StockReceipt
    form_class = StockReceiptForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Wareneingang erstellen'
        return context

    def get_success_url(self):
        return reverse('erp:stockreceipt_detail', kwargs={'pk': self.object.pk})


class StockReceiptDetailView(ErpViewMixin, DetailView):
    model = StockReceipt
    template_name = 'erp/stockreceipt_detail.html'
    context_object_name = 'receipt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_form'] = StockReceiptItemForm()
        context['items'] = self.object.items.select_related('product').all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_erp(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return self.get(request, *args, **kwargs)

        if 'add_item' in request.POST:
            form = StockReceiptItemForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.receipt = self.object
                item.save()
                if item.product:
                    if item.competitor_price_net is None:
                        provider = get_provider()
                        if provider:
                            try:
                                fetched = provider.fetch_price(item.product)
                            except Exception:
                                fetched = None
                            if fetched is not None:
                                item.competitor_price_net = fetched
                                item.save(update_fields=['competitor_price_net'])
                    update_fields = {
                        'stock_qty': models.F('stock_qty') + item.quantity,
                        'cost_net': item.unit_cost_net,
                    }
                    if item.competitor_price_net:
                        update_fields['competitor_price_net'] = item.competitor_price_net
                    Product.objects.filter(id=item.product_id).update(**update_fields)
                    product = Product.objects.get(id=item.product_id)
                    apply_pricing(product, cost_net=item.unit_cost_net, competitor_net=item.competitor_price_net)
                messages.success(request, 'Wareneingang gebucht.')
            else:
                messages.error(request, 'Bitte pruefe den Wareneingang.')
        return self.get(request, *args, **kwargs)

        return self.get(request, *args, **kwargs)


class CompetitorDebugView(ErpViewMixin, TemplateView):
    template_name = 'erp/competitor_debug.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['debug'] = cache.get('erp_geizhals_last_debug')
        return context


class PricingHelpView(ErpViewMixin, TemplateView):
    template_name = 'erp/pricing_help.html'


class CourseListView(ErpViewMixin, ListView):
    model = Course
    template_name = 'erp/course_list.html'
    context_object_name = 'courses'
    paginate_by = 25

    def get_queryset(self):
        qs = Course.objects.all()
        status = self.request.GET.get('status')
        customer = self.request.GET.get('customer')
        instructor = self.request.GET.get('instructor')
        sort = (self.request.GET.get('sort') or '-created_at').strip()
        if status:
            qs = qs.filter(status=status)
        if customer:
            qs = qs.filter(customer_id=customer)
        if instructor:
            qs = qs.filter(instructor_id=instructor)
        allowed_sorts = {'created_at', '-created_at', 'start_date', '-start_date', 'title', '-title'}
        if sort not in allowed_sorts:
            sort = '-created_at'
        return qs.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Course.STATUS_CHOICES
        context['customers'] = Customer.objects.all().order_by('name')
        context['instructors'] = Instructor.objects.all().order_by('name')
        context['filters'] = {
            'status': self.request.GET.get('status', ''),
            'customer': self.request.GET.get('customer', ''),
            'instructor': self.request.GET.get('instructor', ''),
        }
        context['list_sort_options'] = [
            ('-created_at', 'Neueste zuerst'),
            ('created_at', 'Älteste zuerst'),
            ('title', 'Titel A-Z'),
            ('-title', 'Titel Z-A'),
            ('-start_date', 'Start spaeter'),
            ('start_date', 'Start frueher'),
        ]
        context['current_sort'] = (self.request.GET.get('sort') or '-created_at')
        return context


class CourseDetailView(ErpViewMixin, DetailView):
    model = Course
    template_name = 'erp/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        days = course._calc_days()
        instructor_daily = course.instructor_daily_cost
        instructor_cost = instructor_daily * days
        mobile_cost = course.mobile_classroom_cost if course.mobile_classroom_required else 0
        subtotal = instructor_cost + course.expenses + course.lodging + mobile_cost
        context['pricing'] = {
            'days': days,
            'instructor_daily': instructor_daily,
            'instructor_cost': instructor_cost,
            'expenses': course.expenses,
            'lodging': course.lodging,
            'mobile_cost': mobile_cost,
            'subtotal': subtotal,
            'vat_rate': course.vat_rate,
            'price_net': course.price_net,
            'price_gross': course.price_gross,
        }
        return context


class CourseCreateView(ErpEditMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Kurs erstellen'
        return context

    def get_success_url(self):
        return reverse('erp:courses')


class CourseUpdateView(ErpEditMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'erp/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Kurs bearbeiten'
        return context

    def get_success_url(self):
        return reverse('erp:courses')


class ErpHelpView(ErpViewMixin, TemplateView):
    template_name = 'erp/help.html'


class ErpPluginHubView(ErpViewMixin, TemplateView):
    template_name = 'erp/plugins/hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plugins'] = Plugin.objects.all().order_by('-uploaded_at')
        return context
