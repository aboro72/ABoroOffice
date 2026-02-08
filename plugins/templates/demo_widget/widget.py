from apps.cloude.cloude_apps.plugins.widgets import DashboardWidgetProvider
from apps.cloude.cloude_apps.plugins.models import Plugin


class DemoWidgetProvider(DashboardWidgetProvider):
    widget_id = "demo_widget"
    widget_name = "Demo Widget"
    widget_icon = "bi-lightbulb"
    widget_size = "medium"
    widget_order = 30

    def get_context(self, request):
        settings = {}
        try:
            plugin = Plugin.objects.get(slug='demo-widget')
            settings = plugin.settings or {}
        except Exception:
            settings = {}

        title = settings.get('title', 'Demo Plugin')
        city = settings.get('city', 'Berlin')

        return {
            "title": title,
            "city": city,
            "user": request.user.username,
        }

    def get_template_name(self):
        return "demo_widget/widget.html"
