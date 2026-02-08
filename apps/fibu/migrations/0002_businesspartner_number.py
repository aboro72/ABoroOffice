from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fibu', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesspartner',
            name='partner_number',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
