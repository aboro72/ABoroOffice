"""
Development Django settings for ABoroOffice.
Override base settings for development environment.
"""

from .base import *  # noqa: F401, F403

# Development-specific settings
DEBUG = True
ALLOWED_HOSTS = ['*']

# Django extensions for development
INSTALLED_APPS += [  # noqa: F405
    'django_extensions',
]

# Debug toolbar for development (optional)
DEBUG_TOOLBAR_INSTALLED = False
if DEBUG_TOOLBAR_INSTALLED:
    INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405
    INTERNAL_IPS = ['127.0.0.1']

# Disable security checks in development
CSRF_TRUSTED_ORIGINS = ['http://localhost:*', 'http://127.0.0.1:*']
SESSION_COOKIE_SECURE = False

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging for development (more verbose)
LOGGING['loggers']['django']['level'] = 'DEBUG'  # noqa: F405
LOGGING['loggers']['apps']['level'] = 'DEBUG'  # noqa: F405

# Allow all CORS origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Database configuration for development
# Default SQLite is fine, but PostgreSQL is recommended
DATABASES = {  # noqa: F405
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

# Cache - local memory is fine for development
CACHES = {  # noqa: F405
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'aboro-dev-cache',
    }
}

# License check disabled by default in development
LICENSE_CHECK_ENABLED = False  # noqa: F405

# Settings for development purposes
SHELL_PLUS_PRE_IMPORTS = [
    ('apps.licensing.license_manager', 'LicenseManager'),
    ('apps.core.models', 'ABoroUser'),
]

# print("✓ ABoroOffice Development Settings Loaded")  # ✓ Checkmark causes Unicode issues on Windows
print("[OK] ABoroOffice Development Settings Loaded")
