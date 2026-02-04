from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("admin_panel", "0009_systemsettings_imap_full_sync_completed_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="helpdesk_audit_logs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
