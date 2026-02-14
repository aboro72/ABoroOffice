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
        app_switcher = []
        def add_app(key, label, url, icon, can_view=True):
            if app_toggles.get(key, False) and can_view:
                app_switcher.append({
                    'key': key,
                    'label': label,
                    'url': url,
                    'icon': icon,
                })
        add_app('crm', 'CRM', '/crm/', 'fa-solid fa-chart-line', can_view_crm(request.user))
        add_app('erp', 'ERP', '/erp/', 'fa-solid fa-boxes-stacked', can_view_erp(request.user))
        add_app('projects', 'Projekte', '/projects/', 'fa-solid fa-diagram-project')
        add_app('personnel', 'Personal', '/personnel/', 'fa-solid fa-users')
        add_app('fibu', 'FiBu', '/fibu/', 'fa-solid fa-file-invoice-dollar')
        add_app('workflows', 'Workflows', '/workflows/', 'fa-solid fa-gear')
        add_app('marketing', 'Marketing', '/marketing/', 'fa-solid fa-bullhorn')
        add_app('contracts', 'Verträge', '/contracts/', 'fa-solid fa-file-contract')

        return {
            'system_settings': settings_obj,
            'app_toggles': app_toggles,
            'approvals_enabled': app_toggles['approvals'],
            'crm_can_view': can_view_crm(request.user),
            'crm_can_edit': can_edit_crm(request.user),
            'erp_can_view': can_view_erp(request.user),
            'app_switcher': app_switcher,
            'global_search_query': (request.GET.get('q') or '').strip(),
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
            'app_switcher': [],
            'global_search_query': '',
        }

