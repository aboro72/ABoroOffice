from django.apps import AppConfig


class ErpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.erp'

    def ready(self):
        from . import signals  # noqa: F401
    verbose_name = 'ERP'
