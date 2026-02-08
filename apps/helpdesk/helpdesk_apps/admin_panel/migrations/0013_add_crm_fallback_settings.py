from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_panel", "0012_add_plugin_dashboard_position"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="crm_fallback_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Nutze Such-APIs als Notfall-Fallback, wenn die Primärquelle 0 Treffer liefert",
                verbose_name="CRM Fallback aktiviert",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_fallback_provider_order",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Beispiel: ["serpapi", "dataforseo", "bing"]',
                verbose_name="CRM Fallback Provider (Reihenfolge)",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_serpapi_key",
            field=models.CharField(
                blank=True,
                help_text="API Key für SerpAPI (Google Search)",
                max_length=255,
                verbose_name="SerpAPI Key",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_dataforseo_login",
            field=models.CharField(
                blank=True,
                help_text="Login (E-Mail) für DataForSEO",
                max_length=255,
                verbose_name="DataForSEO Login",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_dataforseo_password",
            field=models.CharField(
                blank=True,
                help_text="Passwort für DataForSEO",
                max_length=255,
                verbose_name="DataForSEO Password",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="crm_bing_api_key",
            field=models.CharField(
                blank=True,
                help_text="API Key für Microsoft Bing Web Search",
                max_length=255,
                verbose_name="Bing Search API Key",
            ),
        ),
    ]
