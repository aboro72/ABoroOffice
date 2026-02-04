from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.helpdesk.helpdesk_apps.api'
    label = 'helpdesk_api'
    verbose_name = 'REST API'
