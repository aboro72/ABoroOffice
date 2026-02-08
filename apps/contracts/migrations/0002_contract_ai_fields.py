from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="ai_summary",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="contract",
            name="ai_risks",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="contract",
            name="ai_checklist",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="contract",
            name="ai_key_dates",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="contract",
            name="ai_last_analyzed",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
