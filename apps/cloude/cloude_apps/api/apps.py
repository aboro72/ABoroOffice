from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cloude.cloude_apps.api'
    label = 'cloude_api'
    verbose_name = 'API'
