from django.db import migrations


def seed_minimal_accounts(apps, schema_editor):
    Account = apps.get_model('fibu', 'Account')
    CostCenter = apps.get_model('fibu', 'CostCenter')
    FibuSettings = apps.get_model('fibu', 'FibuSettings')

    accounts = [
        ('1000', 'Kasse', 'asset'),
        ('1200', 'Bank', 'asset'),
        ('1400', 'Forderungen aus Lieferungen und Leistungen', 'asset'),
        ('1600', 'Verbindlichkeiten aus Lieferungen und Leistungen', 'liability'),
        ('3200', 'Warenlager', 'asset'),
        ('3400', 'Wareneingang', 'expense'),
        ('8400', 'Umsatzerlöse 19% USt', 'income'),
        ('8300', 'Umsatzerlöse 7% USt', 'income'),
        ('1576', 'Vorsteuer 19%', 'asset'),
        ('1571', 'Vorsteuer 7%', 'asset'),
        ('1776', 'Umsatzsteuer 19%', 'liability'),
        ('1771', 'Umsatzsteuer 7%', 'liability'),
    ]

    account_map = {}
    for code, name, account_type in accounts:
        obj, _ = Account.objects.get_or_create(
            code=code,
            defaults={'name': name, 'account_type': account_type, 'is_active': True},
        )
        account_map[code] = obj

    settings_obj, _ = FibuSettings.objects.get_or_create(id=1)

    def _set_if_empty(field, value):
        if getattr(settings_obj, field + '_id', None) is None and value is not None:
            setattr(settings_obj, field, value)

    _set_if_empty('receivable_account', account_map.get('1400'))
    _set_if_empty('revenue_account', account_map.get('8400'))
    _set_if_empty('vat_output_account', account_map.get('1776'))
    _set_if_empty('inventory_account', account_map.get('3200'))
    _set_if_empty('payable_account', account_map.get('1600'))
    _set_if_empty('expense_account', account_map.get('3400'))

    if settings_obj.default_cost_center_id is None:
        settings_obj.default_cost_center = CostCenter.objects.filter(code='KST-100').first()

    settings_obj.save()


def unseed_minimal_accounts(apps, schema_editor):
    Account = apps.get_model('fibu', 'Account')
    Account.objects.filter(code__in=['1000','1200','1400','1600','3200','3400','8400','8300','1576','1571','1776','1771']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('fibu', '0004_fibusettings'),
    ]

    operations = [
        migrations.RunPython(seed_minimal_accounts, unseed_minimal_accounts),
    ]
