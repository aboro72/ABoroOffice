from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.helpdesk.helpdesk_apps.admin_panel'
    verbose_name = 'Administration Panel'

    def ready(self):
        """Register signal handlers when app is ready"""
        import apps.helpdesk.helpdesk_apps.admin_panel.signals  # noqa
