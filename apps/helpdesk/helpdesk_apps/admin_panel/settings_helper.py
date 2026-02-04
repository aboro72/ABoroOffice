"""
Helper functions to get system settings from database
Used by email_handler and other components
"""

import os
from django.conf import settings as django_settings


def get_imap_settings():
    """
    Get IMAP settings from database, with fallback to environment variables

    Returns:
        dict: IMAP configuration
    """
    try:
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
        system_settings = SystemSettings.get_settings()

        return {
            'enabled': system_settings.imap_enabled,
            'host': system_settings.imap_host or os.environ.get('IMAP_HOST', 'mail.aboro-it.net'),
            'port': system_settings.imap_port or int(os.environ.get('IMAP_PORT', 993)),
            'username': system_settings.imap_username or os.environ.get('IMAP_USERNAME', ''),
            'password': system_settings.imap_password or os.environ.get('IMAP_PASSWORD', ''),
            'folder': system_settings.imap_folder or os.environ.get('IMAP_FOLDER', 'INBOX'),
            'use_ssl': system_settings.imap_use_ssl,
        }
    except Exception as e:
        # Fallback if database is not available
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not get IMAP settings from database: {str(e)}")

        return {
            'enabled': os.environ.get('IMAP_ENABLED', 'False') == 'True',
            'host': os.environ.get('IMAP_HOST', 'mail.aboro-it.net'),
            'port': int(os.environ.get('IMAP_PORT', 993)),
            'username': os.environ.get('IMAP_USERNAME', ''),
            'password': os.environ.get('IMAP_PASSWORD', ''),
            'folder': os.environ.get('IMAP_FOLDER', 'INBOX'),
            'use_ssl': True,
        }


def get_smtp_settings():
    """
    Get SMTP settings from database, with fallback to environment variables

    Returns:
        dict: SMTP configuration
    """
    try:
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
        system_settings = SystemSettings.get_settings()

        return {
            'host': system_settings.smtp_host or os.environ.get('SMTP_HOST', 'smtp.office365.com'),
            'port': system_settings.smtp_port or int(os.environ.get('SMTP_PORT', 587)),
            'username': system_settings.smtp_username or os.environ.get('EMAIL_USERNAME', ''),
            'password': system_settings.smtp_password or os.environ.get('EMAIL_PASSWORD', ''),
            'use_tls': system_settings.smtp_use_tls,
            'use_ssl': system_settings.smtp_use_ssl,
        }
    except Exception as e:
        # Fallback if database is not available
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not get SMTP settings from database: {str(e)}")

        return {
            'host': os.environ.get('SMTP_HOST', 'smtp.office365.com'),
            'port': int(os.environ.get('SMTP_PORT', 587)),
            'username': os.environ.get('EMAIL_USERNAME', ''),
            'password': os.environ.get('EMAIL_PASSWORD', ''),
            'use_tls': os.environ.get('EMAIL_USE_TLS', 'True') == 'True',
            'use_ssl': False,
        }
