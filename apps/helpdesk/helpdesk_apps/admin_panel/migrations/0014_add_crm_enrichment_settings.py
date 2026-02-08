from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_panel", "0013_add_crm_fallback_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="crm_enrichment_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Optionale Enrichment-APIs für E-Mail/Domain-Daten aktivieren",
                verbose_name="CRM Enrichment aktiviert",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_enrichment_provider_order",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Beispiel: ["hunter", "dropcontact", "clearbit"]',
                verbose_name="CRM Enrichment Provider (Reihenfolge)",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_hunter_api_key",
            field=models.CharField(
                blank=True,
                help_text="API Key für Hunter.io",
                max_length=255,
                verbose_name="Hunter API Key",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_dropcontact_api_key",
            field=models.CharField(
                blank=True,
                help_text="API Key für Dropcontact",
                max_length=255,
                verbose_name="Dropcontact API Key",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_clearbit_api_key",
            field=models.CharField(
                blank=True,
                help_text="API Key für Clearbit",
                max_length=255,
                verbose_name="Clearbit API Key",
            ),
        ),
    ]
