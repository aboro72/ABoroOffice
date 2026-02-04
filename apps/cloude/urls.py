"""
URL configuration for Cloude integration.
Mounted under /cloudstorage/.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    # Home -> login
    path('', RedirectView.as_view(url='/cloudstorage/accounts/login/', permanent=False), name='cloude-home'),

    # Accounts
    path('accounts/', include('apps.cloude.cloude_apps.accounts.urls', namespace='accounts')),

    # Core app
    path('core/', include('apps.cloude.cloude_apps.core.urls', namespace='core')),

    # Storage and Sharing
    path('storage/', include('apps.cloude.cloude_apps.storage.urls', namespace='storage')),
    path('sharing/', include('apps.cloude.cloude_apps.sharing.urls', namespace='sharing')),
]

# Optional API routes (only if DRF is installed)
try:
    import rest_framework  # noqa: F401
except Exception:
    rest_framework = None

if rest_framework is not None:
    from apps.cloude.cloude_apps.api import views as api_views

    urlpatterns += [
        path('api/', include('apps.cloude.cloude_apps.api.urls', namespace='cloude_api')),
        # Non-namespaced alias for legacy templates
        path('api/plugins/discover/', api_views.PluginDiscoverView.as_view(), name='plugin_discover'),
    ]

    # API schema/docs are optional (drf-spectacular may be absent)
    try:
        from drf_spectacular.views import (
            SpectacularAPIView,
            SpectacularSwaggerView,
            SpectacularRedocView,
        )
        from rest_framework.permissions import IsAdminUser
    except Exception:
        SpectacularAPIView = SpectacularSwaggerView = SpectacularRedocView = None

    if SpectacularAPIView and SpectacularSwaggerView and SpectacularRedocView:
        class CloudeSwaggerView(SpectacularSwaggerView):
            """Ensure script_url is present in context to avoid template errors."""
            schema = None
            permission_classes = [IsAdminUser]

            def get(self, request, *args, **kwargs):
                response = super().get(request, *args, **kwargs)
                if isinstance(response.data, dict) and 'script_url' not in response.data:
                    response.data['script_url'] = None
                return response

        class CloudeSchemaView(SpectacularAPIView):
            permission_classes = [IsAdminUser]

        class CloudeRedocView(SpectacularRedocView):
            permission_classes = [IsAdminUser]

        urlpatterns += [
            path('api/schema/', CloudeSchemaView.as_view(), name='cloude-schema'),
            path('api/docs/', CloudeSwaggerView.as_view(url_name='cloude-schema'), name='cloude-swagger'),
            path('api/redoc/', CloudeRedocView.as_view(url_name='cloude-schema'), name='cloude-redoc'),
        ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
