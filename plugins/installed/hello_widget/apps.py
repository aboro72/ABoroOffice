from django.apps import AppConfig
from apps.cloude.cloude_apps.plugins.hooks import hook_registry, UI_DASHBOARD_WIDGET
from .widget import HelloWidgetProvider


class HelloWidgetConfig(AppConfig):
    name = 'hello_widget'

    def ready(self):
        hook_registry.register(UI_DASHBOARD_WIDGET, HelloWidgetProvider, priority=20)
