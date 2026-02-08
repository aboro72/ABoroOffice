from django.apps import AppConfig
from apps.cloude.cloude_apps.plugins.hooks import hook_registry, UI_DASHBOARD_WIDGET
from .widget import DemoWidgetProvider


class DemoWidgetConfig(AppConfig):
    name = 'demo_widget'

    def ready(self):
        hook_registry.register(UI_DASHBOARD_WIDGET, DemoWidgetProvider, priority=30)
