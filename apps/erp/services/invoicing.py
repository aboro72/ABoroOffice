from decimal import Decimal
from django.utils import timezone
from django.db import models
from apps.erp.models import Invoice, SalesOrder, SalesOrderItem, Product


def create_invoice_for_order(order: SalesOrder) -> Invoice:
    order.recalculate_totals()
    customer = order.customer
    invoice = Invoice.objects.create(
        order=order,
        number='',
        status='issued',
        issue_date=timezone.now().date(),
        due_date=None,
        billing_name=customer.name if customer else '',
        billing_address=customer.address if customer else '',
        net_amount=order.net_amount,
        tax_rate=order.tax_rate,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
    )
    order.status = 'invoiced'
    order.save(update_fields=['status'])
    _reduce_stock(order)
    return invoice


def _reduce_stock(order: SalesOrder) -> None:
    items = SalesOrderItem.objects.select_related('product').filter(order=order)
    for item in items:
        if item.product:
            Product.objects.filter(id=item.product_id).update(
                stock_qty=models.F('stock_qty') - item.quantity
            )
