from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0007_staging_enrichment_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="website",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="lead",
            name="address",
            field=models.TextField(blank=True),
        ),
    ]
