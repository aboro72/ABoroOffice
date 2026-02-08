from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0008_lead_website_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='ai_summary',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='ai_next_steps',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='ai_followup_subject',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='lead',
            name='ai_followup_body',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='ai_last_question',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='ai_last_answer',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='ai_last_analyzed',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='ai_status',
            field=models.CharField(default='idle', max_length=20),
        ),
        migrations.AddField(
            model_name='lead',
            name='ai_error',
            field=models.TextField(blank=True),
        ),
    ]
