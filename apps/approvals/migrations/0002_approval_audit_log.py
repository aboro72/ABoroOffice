from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("approvals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalAuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("created", "Created"), ("approved", "Approved"), ("rejected", "Rejected"), ("expired", "Expired"), ("execution_started", "Execution Started"), ("execution_success", "Execution Success"), ("execution_failed", "Execution Failed"), ("email_sent", "Email Sent")], max_length=30)),
                ("actor_label", models.CharField(blank=True, max_length=255)),
                ("method", models.CharField(blank=True, max_length=50)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("actor_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approval_audit_logs", to=settings.AUTH_USER_MODEL)),
                ("approval", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_logs", to="approvals.approval")),
            ],
            options={
                "verbose_name": "Approval Audit Log",
                "verbose_name_plural": "Approval Audit Logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="approvalauditlog",
            index=models.Index(fields=["approval", "-created_at"], name="approvals_a_approv_4bdb2f_idx"),
        ),
        migrations.AddIndex(
            model_name="approvalauditlog",
            index=models.Index(fields=["action", "-created_at"], name="approvals_a_action_1c0dbf_idx"),
        ),
    ]
