from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cloude.cloude_apps.core'
    label = 'cloude_core'
    verbose_name = 'Core'

    def ready(self):
        """Import signals when app is ready"""
        import apps.cloude.cloude_apps.core.signals  # noqa

        # TODO: Register built-in dashboard widgets when plugin system is available
