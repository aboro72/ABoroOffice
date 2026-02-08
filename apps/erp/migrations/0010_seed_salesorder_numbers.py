from django.db import migrations


def seed_order_numbers(apps, schema_editor):
    SalesOrder = apps.get_model('erp', 'SalesOrder')
    NumberSequence = apps.get_model('erp', 'NumberSequence')

    seq, _ = NumberSequence.objects.get_or_create(key='sales_order', defaults={'last_number': 0})
    last = seq.last_number

    for order in SalesOrder.objects.filter(order_number='').order_by('id'):
        last += 1
        order.order_number = f"SO-{order.created_at.year}-{last:05d}"
        order.save(update_fields=['order_number'])

    if last != seq.last_number:
        seq.last_number = last
        seq.save(update_fields=['last_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0009_numbersequence_salesorder_order_number_dunningnotice_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_order_numbers, migrations.RunPython.noop),
    ]
