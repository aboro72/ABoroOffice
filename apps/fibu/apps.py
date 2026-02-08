from django.apps import AppConfig


class FibuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fibu'
    verbose_name = 'FiBu'

    def ready(self):
        from . import signals  # noqa: F401
