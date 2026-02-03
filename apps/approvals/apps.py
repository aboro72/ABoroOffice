"""
Django App Configuration for Approvals
"""

from django.apps import AppConfig


class ApprovalsConfig(AppConfig):
    """Configuration for the approvals app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.approvals'
    verbose_name = 'SSH Approvals Workflow'

    def ready(self):
        """Import signals when app is ready."""
        import apps.approvals.signals  # noqa: F401
