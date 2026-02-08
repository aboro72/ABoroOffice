from django.utils import timezone
from apps.erp.models import SalesOrder, SalesOrderItem, Quote, QuoteItem, OrderConfirmation
from apps.erp.services.numbering import next_number
from django.apps import apps


def create_order_from_quote(quote: Quote) -> SalesOrder:
    order = SalesOrder.objects.create(
        customer=quote.customer,
        status='confirmed',
        tax_rate=quote.tax_rate,
        contract=None,
    )
    items = QuoteItem.objects.filter(quote=quote).select_related('product')
    for item in items:
        SalesOrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
    order.recalculate_totals()
    OrderConfirmation.objects.create(order=order, status='sent')
    quote.status = 'accepted'
    quote.save(update_fields=['status'])
    try:
        Project = apps.get_model('projects', 'Project')
        Project.objects.create(
            name=f"Auftrag {order.order_number or order.id}",
            status='active',
            start_date=timezone.now().date(),
            erp_quote=quote,
            erp_order=order,
        )
    except Exception:
        pass
    return order
