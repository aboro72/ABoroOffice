from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0002_contract_ai_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="ai_status",
            field=models.CharField(default="idle", max_length=20),
        ),
        migrations.AddField(
            model_name="contract",
            name="ai_error",
            field=models.TextField(blank=True),
        ),
    ]
