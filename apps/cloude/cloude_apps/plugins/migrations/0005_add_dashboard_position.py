from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plugins", "0004_add_plugin_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="plugin",
            name="dashboard_position",
            field=models.CharField(
                choices=[
                    ("inherit", "Inherit Dashboard Setting"),
                    ("top", "Top"),
                    ("bottom", "Bottom"),
                    ("left", "Left"),
                    ("right", "Right"),
                    ("center", "Center"),
                ],
                default="inherit",
                help_text="Position on main dashboard (top/bottom/left/right/center)",
                max_length=20,
            ),
        ),
    ]
