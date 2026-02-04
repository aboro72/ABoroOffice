from django.apps import AppConfig

class HelpDeskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.helpdesk'
    verbose_name = 'HelpDesk Suite'

    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.helpdesk.helpdesk_apps.tickets.signals
        except (ImportError, RuntimeError):
            pass
