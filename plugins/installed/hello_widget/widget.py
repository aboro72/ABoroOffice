from apps.cloude.cloude_apps.plugins.widgets import DashboardWidgetProvider


class HelloWidgetProvider(DashboardWidgetProvider):
    widget_id = 'hello_widget'
    widget_name = 'Hello Widget'
    widget_icon = 'bi-emoji-smile'
    widget_size = 'small'

    def get_css_classes(self) -> str:
        return 'col-md-3'
    widget_order = 20

    def get_context(self, request):
        return {'message': f'Hallo {request.user.username}!'}

    def get_template_name(self):
        return 'hello_widget/widget.html'
