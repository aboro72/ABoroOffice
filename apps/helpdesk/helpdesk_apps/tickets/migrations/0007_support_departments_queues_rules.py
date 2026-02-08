from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('tickets', '0006_ticket_created_from_email_ticket_email_from_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportDepartment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created at')),
            ],
            options={
                'verbose_name': 'support department',
                'verbose_name_plural': 'support departments',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='SupportQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('default_support_level', models.CharField(choices=[('level_1', 'Level 1 - First Line Support'), ('level_2', 'Level 2 - Technical Support'), ('level_3', 'Level 3 - Expert Support'), ('level_4', 'Level 4 - Senior Expert')], default='level_1', max_length=10, verbose_name='default support level')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created at')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='queues', to='tickets.supportdepartment', verbose_name='department')),
            ],
            options={
                'verbose_name': 'support queue',
                'verbose_name_plural': 'support queues',
                'ordering': ['department__name', 'name'],
                'unique_together': {('department', 'name')},
            },
        ),
        migrations.CreateModel(
            name='TicketRoutingRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='name')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('contains_text', models.CharField(blank=True, help_text='Simple keyword match against title/description.', max_length=120, verbose_name='contains text')),
                ('priority', models.CharField(blank=True, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], max_length=20, verbose_name='priority')),
                ('support_level', models.CharField(blank=True, choices=[('level_1', 'Level 1 - First Line Support'), ('level_2', 'Level 2 - Technical Support'), ('level_3', 'Level 3 - Expert Support'), ('level_4', 'Level 4 - Senior Expert')], max_length=10, verbose_name='support level')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created at')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='routing_rules', to='tickets.category', verbose_name='category')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='routing_rules', to='tickets.supportdepartment', verbose_name='department')),
                ('queue', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='routing_rules', to='tickets.supportqueue', verbose_name='queue')),
            ],
            options={
                'verbose_name': 'ticket routing rule',
                'verbose_name_plural': 'ticket routing rules',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='supportqueue',
            name='notify_groups',
            field=models.ManyToManyField(blank=True, help_text='Groups that should receive notifications for this queue.', related_name='helpdesk_queues', to='auth.group'),
        ),
        migrations.AddField(
            model_name='supportdepartment',
            name='notify_groups',
            field=models.ManyToManyField(blank=True, help_text='Groups that should receive notifications for this department.', related_name='helpdesk_departments', to='auth.group'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tickets', to='tickets.supportdepartment', verbose_name='department'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='queue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tickets', to='tickets.supportqueue', verbose_name='queue'),
        ),
    ]
