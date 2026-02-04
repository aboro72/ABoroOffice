"""
Context processors for admin app
"""
from django.core.cache import cache
from .models import SystemSettings

# Cache timeout in seconds (5 minutes = 300 seconds)
CACHE_TIMEOUT = 300


def admin_settings_context(request):
    """
    Add admin settings to context for all templates.
    Uses caching to reduce database queries.
    """
    try:
        # Try to get settings from cache first
        cache_key = 'admin_system_settings'
        settings = cache.get(cache_key)

        # If not in cache, fetch from database and cache it
        if settings is None:
            settings = SystemSettings.get_settings()
            cache.set(cache_key, settings, CACHE_TIMEOUT)

        return {
            'system_settings': settings,
            'text_editor': settings.text_editor,
            'admin_app_name': settings.app_name,
            'admin_company_name': settings.company_name,
            'admin_logo': settings.logo,
            'admin_logo_url': settings.logo.url if settings.logo else None,
            'stats_permissions': settings.get_stats_permissions(),
        }
    except Exception as e:
        # Fallback to defaults if something goes wrong
        return {
            'system_settings': None,
            'text_editor': 'tinymce',
            'admin_app_name': 'Helpdesk',
            'admin_company_name': 'Company',
            'admin_logo': None,
            'admin_logo_url': None,
            'stats_permissions': {'admin': True, 'support_agent': False, 'customer': False},
        }
