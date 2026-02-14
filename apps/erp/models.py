from decimal import Decimal
from datetime import datetime, time
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('business', 'Business'),
        ('private', 'Privat'),
    ]

    name = models.CharField(max_length=200)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='business')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True)
    categories = models.ManyToManyField(
        'ProductCategory',
        blank=True,
        related_name='products',
    )
    image = models.ImageField(upload_to='erp/products/', null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_qty = models.IntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)
    cost_net = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'))
    competitor_price_net = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    suggested_price_net = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    suggested_price_gross = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_last_calculated = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    marketing_campaign = models.ForeignKey(
        'marketing.Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='erp_products',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField(max_length=200)
    categories = models.ManyToManyField(
        'ProductCategory',
        blank=True,
        related_name='services',
    )
    image = models.ImageField(upload_to='erp/services/', null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )

    def __str__(self):
        return self.name


class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('new', 'Neu'),
        ('planned', 'Geplant'),
        ('in_progress', 'In Arbeit'),
        ('done', 'Erledigt'),
        ('cancelled', 'Storniert'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    scheduled_for = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='erp_work_orders',
    )
    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='erp_work_orders',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('confirmed', 'Bestätigt'),
        ('invoiced', 'Abgerechnet'),
        ('paid', 'Bezahlt'),
        ('cancelled', 'Storniert'),
    ]

    order_number = models.CharField(max_length=50, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'))
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='erp_sales_orders',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.order_number or f"Order #{self.id}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            from .services.numbering import next_number
            self.order_number = next_number('sales_order', 'SO')
        if self.status in ('confirmed', 'invoiced', 'paid') and not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        subtotal = Decimal('0.00')
        for item in self.items.all():
            subtotal += Decimal(str(item.line_total()))
        tax = (subtotal * Decimal(str(self.tax_rate)) / Decimal('100.00')).quantize(Decimal('0.01'))
        total = subtotal + tax
        self.net_amount = subtotal
        self.tax_amount = tax
        self.total_amount = total
        self.save(update_fields=['net_amount', 'tax_amount', 'total_amount'])


class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def line_total(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        if self.product and not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
        self.order.recalculate_totals()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.recalculate_totals()


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('issued', 'Ausgestellt'),
        ('paid', 'Bezahlt'),
        ('cancelled', 'Storniert'),
    ]

    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='invoices')
    number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    billing_name = models.CharField(max_length=200, blank=True)
    billing_address = models.TextField(blank=True)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            from .services.numbering import next_number
            self.number = next_number('invoice', 'INV')
        if self.status in ('issued', 'paid') and not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
        super().save(*args, **kwargs)


class NumberSequence(models.Model):
    key = models.CharField(max_length=50, unique=True)
    last_number = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.key}: {self.last_number}"


class Quote(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('sent', 'Gesendet'),
        ('accepted', 'Angenommen'),
        ('rejected', 'Abgelehnt'),
    ]

    number = models.CharField(max_length=50, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.number or f"Quote #{self.id}"

    def save(self, *args, **kwargs):
        if not self.number:
            from .services.numbering import next_number
            self.number = next_number('quote', 'AN')
        if self.status != 'draft' and not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.locked_reason = f"Status: {self.status}"
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        subtotal = Decimal('0.00')
        for item in self.items.all():
            subtotal += Decimal(str(item.line_total()))
        tax = (subtotal * Decimal(str(self.tax_rate)) / Decimal('100.00')).quantize(Decimal('0.01'))
        total = subtotal + tax
        self.net_amount = subtotal
        self.tax_amount = tax
        self.total_amount = total
        self.save(update_fields=['net_amount', 'tax_amount', 'total_amount'])


class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def line_total(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        if self.product and not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
        self.quote.recalculate_totals()

    def delete(self, *args, **kwargs):
        quote = self.quote
        super().delete(*args, **kwargs)
        quote.recalculate_totals()


class OrderConfirmation(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Gesendet'),
        ('accepted', 'BestÃ¤tigt'),
    ]

    number = models.CharField(max_length=50, unique=True, blank=True)
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='confirmations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.number or f"OrderConf #{self.id}"

    def save(self, *args, **kwargs):
        if not self.number:
            from .services.numbering import next_number
            self.number = next_number('order_confirmation', 'AB')
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
        super().save(*args, **kwargs)


class DunningNotice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Entwurf'),
        ('sent', 'Gesendet'),
        ('paid', 'Bezahlt'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='dunning_notices')
    number = models.CharField(max_length=50, unique=True, blank=True)
    level = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateField(null=True, blank=True)
    email_subject = models.CharField(max_length=255, blank=True)
    email_body = models.TextField(blank=True)
    letter_text = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.number or f"Dunning #{self.id}"

    def save(self, *args, **kwargs):
        if not self.number:
            from .services.numbering import next_number
            self.number = next_number('dunning', 'MAH')
        if self.status == 'sent' and not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
        super().save(*args, **kwargs)


class StockReceipt(models.Model):
    supplier_name = models.CharField(max_length=200, blank=True)
    receipt_date = models.DateField(default=timezone.now)
    invoice_file = models.FileField(upload_to='erp/stock_receipts/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wareneingang #{self.id}"


class StockReceiptItem(models.Model):
    receipt = models.ForeignKey(StockReceipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_cost_net = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    competitor_price_net = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def line_total(self):
        return self.quantity * self.unit_cost_net


class Course(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Geplant'),
        ('in_progress', 'In Arbeit'),
        ('done', 'Abgeschlossen'),
        ('cancelled', 'Storniert'),
    ]

    event_number = models.CharField(max_length=30, unique=True, blank=True)
    title = models.CharField(max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    instructor = models.ForeignKey('personnel.Instructor', on_delete=models.SET_NULL, null=True, blank=True)
    required_skill = models.ForeignKey('personnel.TeachingSkill', on_delete=models.SET_NULL, null=True, blank=True)
    work_order = models.ForeignKey(
        'WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    contract = models.ForeignKey(
        'contracts.Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    instructor_days = models.PositiveIntegerField(default=1)
    instructor_daily_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lodging = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mobile_classroom_required = models.BooleanField(default=False)
    mobile_classroom_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mobile_classroom_courses'
    )
    mobile_classroom_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.00'))
    price_net = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_gross = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _calc_days(self) -> int:
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days
            return max(1, delta + 1)
        return max(1, int(self.instructor_days or 1))

    def recalculate_price(self):
        days = self._calc_days()
        daily = Decimal(str(self.instructor_daily_cost or 0))
        expenses = Decimal(str(self.expenses or 0))
        lodging = Decimal(str(self.lodging or 0))
        mobile = Decimal('0.00')
        if self.mobile_classroom_required:
            mobile = Decimal(str(self.mobile_classroom_cost or 0))
        net = (daily * Decimal(days)) + expenses + lodging + mobile
        gross = net * (Decimal('1.00') + (Decimal(str(self.vat_rate)) / Decimal('100.00')))
        self.price_net = _round_005(net)
        self.price_gross = _round_005(gross)

    def save(self, *args, **kwargs):
        if not self.event_number:
            self.event_number = _next_event_number()
        if self.instructor and not self.instructor_daily_cost:
            self.instructor_daily_cost = self.instructor.daily_rate
        if self.mobile_classroom_required and self.mobile_classroom_product and not self.mobile_classroom_cost:
            self.mobile_classroom_cost = self.mobile_classroom_product.price
        self.recalculate_price()
        super().save(*args, **kwargs)
        if self.work_order_id is None and self.customer_id:
            scheduled_for = None
            if self.start_date:
                scheduled_for = timezone.make_aware(datetime.combine(self.start_date, time(9, 0)))
            wo = WorkOrder.objects.create(
                customer=self.customer,
                title=f"Veranstaltung {self.event_number} - {self.title}",
                description=self.description or '',
                status='planned',
                scheduled_for=scheduled_for,
                contract=self.contract,
            )
            Course.objects.filter(pk=self.pk, work_order__isnull=True).update(work_order=wo)
            self.work_order = wo

    def __str__(self):
        return f"{self.event_number} - {self.title}" if self.event_number else self.title

    class Meta:
        verbose_name = 'Veranstaltung'
        verbose_name_plural = 'Veranstaltungen'


def _round_005(value: Decimal) -> Decimal:
    return (value * Decimal('20')).quantize(Decimal('1')) / Decimal('20')


def _next_event_number() -> str:
    prefix = timezone.now().strftime("EVT-%Y-")
    last = Course.objects.filter(event_number__startswith=prefix).order_by('-event_number').first()
    if last and last.event_number:
        try:
            num = int(last.event_number.split('-')[-1]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"{prefix}{num:06d}"


class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='registered')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.title} - {self.customer}"
