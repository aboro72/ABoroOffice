from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_panel", "0014_add_crm_enrichment_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="bedrock_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Amazon Bedrock für KI-Funktionen aktivieren",
                verbose_name="Bedrock aktiviert",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="bedrock_api_key",
            field=models.CharField(
                blank=True,
                help_text="Bearer Token für Bedrock API",
                max_length=255,
                verbose_name="Bedrock API Key",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="bedrock_region",
            field=models.CharField(
                default="eu-central-1",
                max_length=50,
                verbose_name="Bedrock Region",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="bedrock_model_id",
            field=models.CharField(
                default="anthropic.claude-3-5-sonnet-20240620-v1:0",
                max_length=200,
                verbose_name="Bedrock Model ID",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="bedrock_max_tokens",
            field=models.IntegerField(
                default=600,
                verbose_name="Bedrock Max Tokens",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="bedrock_temperature",
            field=models.FloatField(
                default=0.2,
                verbose_name="Bedrock Temperature",
            ),
        ),
    ]
