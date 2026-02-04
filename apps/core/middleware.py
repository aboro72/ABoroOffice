from django.http import Http404
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


class AppToggleMiddleware:
    """Block access to disabled apps based on SystemSettings.app_toggles."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or '/'

        # Always allow core admin/system paths
        allow_prefixes = (
            '/admin/',
            '/admin-dashboard/',
            '/system-settings/',
            '/api-docs/',
            '/login/',
            '/static/',
            '/media/',
        )
        if path.startswith(allow_prefixes):
            return self.get_response(request)

        # Allow auth paths even if cloudstorage is disabled
        if path.startswith('/cloudstorage/accounts/') or path.startswith('/accounts/'):
            return self.get_response(request)

        try:
            toggles = SystemSettings.get_settings().app_toggles or {}
        except Exception:
            toggles = {}

        def is_enabled(key, default=True):
            return bool(toggles.get(key, default))

        # Block paths based on toggles
        if path.startswith('/approvals/') and not is_enabled('approvals', False):
            raise Http404()
        if path.startswith('/classroom/') and not is_enabled('classroom', True):
            raise Http404()
        if path.startswith('/helpdesk/') and not is_enabled('helpdesk', True):
            raise Http404()
        if (
            path.startswith('/cloudstorage/')
            or path.startswith('/storage/')
            or path.startswith('/sharing/')
            or path.startswith('/core/')
        ) and not is_enabled('cloudstorage', True):
            raise Http404()

        return self.get_response(request)
