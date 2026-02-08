from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('counterparty', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('draft', 'Entwurf'), ('active', 'Aktiv'), ('expired', 'Abgelaufen'), ('terminated', 'Beendet')], default='draft', max_length=20)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('renewal_date', models.DateField(blank=True, null=True)),
                ('value_eur', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('file', models.FileField(blank=True, upload_to='contracts/')),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contracts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ContractVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(default='v1', max_length=100)),
                ('file', models.FileField(blank=True, upload_to='contracts/versions/')),
                ('summary', models.TextField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='contracts.contract')),
            ],
        ),
    ]
