from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cloude.cloude_apps.accounts'
    verbose_name = 'Accounts'

    def ready(self):
        """Import signals when app is ready"""
        import apps.cloude.cloude_apps.accounts.signals  # noqa
