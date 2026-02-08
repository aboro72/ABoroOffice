"""
Production Django settings for ABoroOffice.
Override base settings for production environment.
"""

import os
from .base import *  # noqa: F401, F403

# Production-specific settings
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'aboro.office').split(',')

# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Remove debug toolbar in production
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']  # noqa: F405
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405

# Database configuration for production
DATABASES = {  # noqa: F405
    'default': build_database_config(default_engine='postgresql'),  # noqa: F405
}

# Cache configuration for production (use Redis)
CACHES = {  # noqa: F405
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_KWARGS': {'max_connections': 50},
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        }
    }
}

# Session configuration for production
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@aboro.office')

# Celery configuration for production
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Berlin'

# Static and media files in production
STATIC_URL = '/static/'
STATIC_ROOT = os.getenv('STATIC_ROOT', '/var/www/aboro/static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/aboro/media')

# Storage configuration (S3 for large deployments)
# AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
# AWS_S3_ACCESS_KEY_ID = os.getenv('AWS_S3_ACCESS_KEY_ID')
# AWS_S3_SECRET_ACCESS_KEY = os.getenv('AWS_S3_SECRET_ACCESS_KEY')
# if AWS_STORAGE_BUCKET_NAME:
#     STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/static/'
#     DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Logging for production (only errors and above)
LOGGING = {  # noqa: F405
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.getenv('LOG_DIR', '/var/log/aboro') + '/aboro.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.getenv('LOG_DIR', '/var/log/aboro') + '/aboro_error.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'error_file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Sentry configuration (optional)
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False
    )

# License check enabled in production
LICENSE_CHECK_ENABLED = True  # noqa: F405

print("✓ ABoroOffice Production Settings Loaded")
