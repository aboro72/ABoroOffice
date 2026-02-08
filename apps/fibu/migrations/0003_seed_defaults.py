from django.db import migrations


def seed_defaults(apps, schema_editor):
    Account = apps.get_model('fibu', 'Account')
    CostCenter = apps.get_model('fibu', 'CostCenter')
    CostType = apps.get_model('fibu', 'CostType')

    account_data = [
        ('KST-100', 'Kostenstellen Verwaltung', 'expense'),
        ('KST-200', 'Kostenstellen Vertrieb', 'expense'),
        ('KST-300', 'Kostenstellen Produktion/Service', 'expense'),
        ('KST-400', 'Kostenstellen IT/IuK', 'expense'),
        ('KST-500', 'Kostenstellen Orga', 'expense'),
        ('KST-900', 'Kostenstellen Projekte', 'expense'),
    ]

    accounts = {}
    for code, name, account_type in account_data:
        account, _ = Account.objects.get_or_create(
            code=code,
            defaults={'name': name, 'account_type': account_type, 'is_active': True},
        )
        accounts[code] = account

    centers = [
        ('KST-100', 'Verwaltung', 'main', 'KST-100'),
        ('KST-200', 'Vertrieb', 'main', 'KST-200'),
        ('KST-300', 'Produktion/Service', 'main', 'KST-300'),
        ('KST-400', 'IT/IuK', 'support', 'KST-400'),
        ('KST-500', 'Orga', 'support', 'KST-500'),
        ('KST-900', 'Projekte', 'project', 'KST-900'),
    ]

    for code, name, cc_type, acc_code in centers:
        CostCenter.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'cost_center_type': cc_type,
                'account': accounts.get(acc_code),
                'description': 'Default Kostenstelle (SKR04 Basisplan).',
                'is_active': True,
            },
        )

    cost_types = [
        ('PERS', 'Personalaufwand', 'Löhne, Gehälter, Sozialabgaben'),
        ('MATERIAL', 'Materialaufwand', 'Wareneinsatz, Verbrauchsmaterialien'),
        ('MIETE', 'Miete & Nebenkosten', 'Miete, NK, Wartung'),
        ('ENERGIE', 'Energie', 'Strom, Gas, Wasser'),
        ('REISE', 'Reise & Spesen', 'Reisekosten, Spesen, Unterkunft'),
        ('IT', 'IT & Software', 'Lizenzen, Hardware, Services'),
        ('MARKETING', 'Marketing & Vertrieb', 'Werbung, Kampagnen'),
        ('SONST', 'Sonstiges', 'Sonstige Kosten'),
    ]

    for code, name, desc in cost_types:
        CostType.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})


def unseed_defaults(apps, schema_editor):
    Account = apps.get_model('fibu', 'Account')
    CostCenter = apps.get_model('fibu', 'CostCenter')
    CostType = apps.get_model('fibu', 'CostType')

    CostType.objects.filter(code__in=[
        'PERS', 'MATERIAL', 'MIETE', 'ENERGIE', 'REISE', 'IT', 'MARKETING', 'SONST'
    ]).delete()

    CostCenter.objects.filter(code__in=[
        'KST-100', 'KST-200', 'KST-300', 'KST-400', 'KST-500', 'KST-900'
    ]).delete()

    Account.objects.filter(code__in=[
        'KST-100', 'KST-200', 'KST-300', 'KST-400', 'KST-500', 'KST-900'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('fibu', '0002_businesspartner_number'),
    ]

    operations = [
        migrations.RunPython(seed_defaults, unseed_defaults),
    ]
