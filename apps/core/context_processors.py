from django.conf import settings
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
from apps.crm.permissions import can_view_crm, can_edit_crm
from apps.erp.permissions import can_view_erp


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
            'crm': toggles.get('crm', False),
            'contracts': toggles.get('contracts', False),
            'marketing': toggles.get('marketing', False),
            'erp': toggles.get('erp', False),
            'personnel': toggles.get('personnel', False),
            'fibu': toggles.get('fibu', False),
            'projects': toggles.get('projects', False),
            'workflows': toggles.get('workflows', False),
        }
        return {
            'system_settings': settings_obj,
            'app_toggles': app_toggles,
            'approvals_enabled': app_toggles['approvals'],
            'crm_can_view': can_view_crm(request.user),
            'crm_can_edit': can_edit_crm(request.user),
            'erp_can_view': can_view_erp(request.user),
        }
    except Exception:
        return {
            'system_settings': None,
            'app_toggles': {
                'approvals': False,
                'helpdesk': True,
                'cloudstorage': True,
                'classroom': True,
                'crm': False,
                'contracts': False,
                'marketing': False,
                'erp': False,
                'personnel': False,
                'fibu': False,
                'projects': False,
                'workflows': False,
            },
            'approvals_enabled': False,
            'crm_can_view': False,
            'crm_can_edit': False,
            'erp_can_view': False,
        }

