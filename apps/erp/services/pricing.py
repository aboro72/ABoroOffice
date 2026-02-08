from decimal import Decimal
from django.utils import timezone
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


def _get_settings():
    return SystemSettings.get_settings()


def _round_005(value: Decimal) -> Decimal:
    return (value * Decimal('20')).quantize(Decimal('1')) / Decimal('20')


def calculate_suggested_prices(cost_net: Decimal, competitor_net: Decimal | None, vat_rate: Decimal) -> tuple[Decimal, Decimal]:
    settings_obj = _get_settings()
    min_margin = Decimal(str(getattr(settings_obj, 'erp_min_margin_pct', 20)))
    undercut_min = Decimal(str(getattr(settings_obj, 'erp_undercut_min_pct', 3)))
    undercut_max = Decimal(str(getattr(settings_obj, 'erp_undercut_max_pct', 10)))
    if undercut_max < undercut_min:
        undercut_max = undercut_min
    undercut = (undercut_min + undercut_max) / Decimal('2')

    base = cost_net * (Decimal('1.00') + (min_margin / Decimal('100.00')))
    target = base
    if competitor_net:
        competitor_target = competitor_net * (Decimal('1.00') - (undercut / Decimal('100.00')))
        if competitor_target > base:
            target = competitor_target

    net = _round_005(target)
    gross = _round_005(net * (Decimal('1.00') + (vat_rate / Decimal('100.00'))))
    return net, gross


def apply_pricing(product, cost_net: Decimal | None = None, competitor_net: Decimal | None = None):
    cost = Decimal(str(cost_net if cost_net is not None else product.cost_net))
    competitor = competitor_net if competitor_net is not None else product.competitor_price_net
    vat_rate = Decimal(str(product.vat_rate or Decimal('19.00')))
    net, gross = calculate_suggested_prices(cost, competitor, vat_rate)
    product.suggested_price_net = net
    product.suggested_price_gross = gross
    product.price_last_calculated = timezone.now()
    product.save(update_fields=['suggested_price_net', 'suggested_price_gross', 'price_last_calculated'])
    return net, gross
