"""
URL configuration for HelpDesk integration.
Mounted under /helpdesk/.
"""

from django.urls import include, path

# Swagger/OpenAPI (optional)
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
except Exception:
    SpectacularAPIView = SpectacularSwaggerView = SpectacularRedocView = None

if SpectacularSwaggerView is not None:
    from rest_framework.permissions import IsAdminUser

    class HelpdeskSwaggerView(SpectacularSwaggerView):
        """Ensure script_url is present in context to avoid template errors."""
        schema = None
        permission_classes = [IsAdminUser]

        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)
            if isinstance(response.data, dict) and 'script_url' not in response.data:
                response.data['script_url'] = None
            return response

    class HelpdeskSchemaView(SpectacularAPIView):
        permission_classes = [IsAdminUser]

    class HelpdeskRedocView(SpectacularRedocView):
        permission_classes = [IsAdminUser]

urlpatterns = [
    # API docs (Helpdesk)
    *([
        path('api/schema/', HelpdeskSchemaView.as_view(urlconf='apps.helpdesk.helpdesk_apps.api.urls'), name='helpdesk-schema'),
        path('api/docs/', HelpdeskSwaggerView.as_view(url_name='helpdesk-schema'), name='helpdesk-swagger'),
        path('api/redoc/', HelpdeskRedocView.as_view(url_name='helpdesk-schema'), name='helpdesk-redoc'),
    ] if SpectacularSwaggerView is not None else []),

    path('auth/', include('apps.helpdesk.auth_urls', namespace='helpdesk_accounts')),
    path('api/', include('apps.helpdesk.helpdesk_apps.api.urls', namespace='api')),
    path('tickets/', include('apps.helpdesk.helpdesk_apps.tickets.urls', namespace='tickets')),
    path('kb/', include('apps.helpdesk.helpdesk_apps.knowledge.urls', namespace='knowledge')),
    path('chat/', include('apps.helpdesk.helpdesk_apps.chat.urls', namespace='chat')),
    path('admin-panel/', include('apps.helpdesk.helpdesk_apps.admin_panel.urls', namespace='admin_panel')),
    path('', include('apps.helpdesk.helpdesk_apps.main.urls', namespace='main')),
]
