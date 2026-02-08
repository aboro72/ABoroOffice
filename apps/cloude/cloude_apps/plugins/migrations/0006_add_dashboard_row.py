from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plugins", "0005_add_dashboard_position"),
    ]

    operations = [
        migrations.AddField(
            model_name="plugin",
            name="dashboard_row",
            field=models.IntegerField(
                default=1,
                help_text="Row order within dashboard position (lower = higher)",
            ),
        ),
    ]
