from django.conf import settings
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


def system_settings_context(request):
    """Provide system settings (theme/branding) for all templates."""
    try:
        settings_obj = SystemSettings.get_settings()
        toggles = settings_obj.app_toggles or {}
        app_toggles = {
            'approvals': toggles.get('approvals', False),
            'helpdesk': toggles.get('helpdesk', True),
            'cloudstorage': toggles.get('cloudstorage', True),
            'classroom': toggles.get('classroom', True),
        }
        return {
            'system_settings': settings_obj,
            'app_toggles': app_toggles,
            'approvals_enabled': app_toggles['approvals'],
        }
    except Exception:
        return {
            'system_settings': None,
            'app_toggles': {
                'approvals': False,
                'helpdesk': True,
                'cloudstorage': True,
                'classroom': True,
            },
            'approvals_enabled': False,
        }
