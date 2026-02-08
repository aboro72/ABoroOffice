from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_panel", "0011_add_app_toggles"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="plugin_dashboard_position",
            field=models.CharField(
                choices=[
                    ("top", "Oben"),
                    ("bottom", "Unten"),
                    ("left", "Links"),
                    ("right", "Rechts"),
                    ("center", "Mitte"),
                ],
                default="bottom",
                help_text="Position des Plugin-Bereichs im Haupt-Dashboard",
                max_length=20,
                verbose_name="Plugin-Bereich Position",
            ),
        ),
    ]
