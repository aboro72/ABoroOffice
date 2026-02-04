from django.apps import AppConfig

class CloudeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cloude'
    verbose_name = 'Cloude Storage Suite'

    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.cloude.cloude_apps.core.signals
        except (ImportError, RuntimeError):
            pass
