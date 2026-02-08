from decimal import Decimal
from django.utils import timezone
from apps.fibu.models import JournalEntry, JournalLine, FibuSettings


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal('0.00')


def post_invoice(invoice):
    settings_obj = FibuSettings.get_settings()
    if not settings_obj.auto_posting_enabled:
        return None
    if JournalEntry.objects.filter(erp_invoice=invoice).exists():
        return None

    if not (settings_obj.receivable_account and settings_obj.revenue_account and settings_obj.vat_output_account):
        return None

    entry = JournalEntry.objects.create(
        date=invoice.issue_date or timezone.now().date(),
        reference=invoice.number,
        description=f'Ausgangsrechnung {invoice.number}',
        erp_invoice=invoice,
    )

    total = _to_decimal(invoice.total_amount)
    net = _to_decimal(invoice.net_amount)
    tax = _to_decimal(invoice.tax_amount)

    JournalLine.objects.create(
        entry=entry,
        account=settings_obj.receivable_account,
        cost_center=settings_obj.default_cost_center,
        debit=total,
        credit=Decimal('0.00'),
        description='Debitor',
    )

    if net > 0:
        JournalLine.objects.create(
            entry=entry,
            account=settings_obj.revenue_account,
            cost_center=settings_obj.default_cost_center,
            debit=Decimal('0.00'),
            credit=net,
            description='Umsatzerlöse',
        )

    if tax > 0:
        JournalLine.objects.create(
            entry=entry,
            account=settings_obj.vat_output_account,
            cost_center=settings_obj.default_cost_center,
            debit=Decimal('0.00'),
            credit=tax,
            description='Umsatzsteuer',
        )

    return entry


def post_stock_receipt(receipt):
    settings_obj = FibuSettings.get_settings()
    if not settings_obj.auto_posting_enabled:
        return None
    if JournalEntry.objects.filter(erp_stockreceipt=receipt).exists():
        return None

    if not (settings_obj.inventory_account and settings_obj.payable_account):
        return None

    total = Decimal('0.00')
    for item in receipt.items.all():
        total += _to_decimal(item.unit_cost_net) * _to_decimal(item.quantity)

    if total <= 0:
        return None

    entry = JournalEntry.objects.create(
        date=receipt.receipt_date or timezone.now().date(),
        reference=f'WE-{receipt.id}',
        description='Wareneingang',
        erp_stockreceipt=receipt,
    )

    JournalLine.objects.create(
        entry=entry,
        account=settings_obj.inventory_account,
        cost_center=settings_obj.default_cost_center,
        debit=total,
        credit=Decimal('0.00'),
        description='Wareneingang',
    )

    JournalLine.objects.create(
        entry=entry,
        account=settings_obj.payable_account,
        cost_center=settings_obj.default_cost_center,
        debit=Decimal('0.00'),
        credit=total,
        description='Kreditor',
    )

    return entry
