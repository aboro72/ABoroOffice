from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('approvals', '0001_initial'),
        ('core', '0002_add_approver_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='aborouser',
            name='approval_groups',
            field=models.ManyToManyField(
                blank=True,
                help_text='Rating schedules this user is allowed to approve',
                related_name='approvers',
                to='approvals.ratingschedule'
            ),
        ),
    ]
