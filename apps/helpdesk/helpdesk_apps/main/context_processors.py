"""
Context processors to make settings available to all templates.
"""
from django.conf import settings


def branding_context(request):
    """
    Add customizable branding settings to template context.

    Makes the following variables available in all templates:
    - app_name: Application name (navbar brand)
    - company_name: Company name for branding
    - logo_url: URL to company logo
    - app_title: Application title for HTML title tags
    """
    return {
        'app_name': getattr(settings, 'APP_NAME', 'ABoroOffice'),
        'company_name': getattr(settings, 'COMPANY_NAME', 'ABoroOffice'),
        'logo_url': getattr(settings, 'LOGO_URL', ''),
        'app_title': getattr(settings, 'APP_TITLE', 'ABoroOffice'),
        'helpdesk_prefix': getattr(settings, 'HELPDESK_URL_PREFIX', ''),
    }
