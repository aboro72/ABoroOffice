"""
Base Django settings for ABoroOffice project.
Shared settings used by all environments (development, production, testing).
"""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / 'apps'

# SECURITY: Secret key should be in .env in production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

def build_database_config(default_engine='sqlite'):
    engine = os.getenv('DB_ENGINE', default_engine).lower()

    if engine in ('sqlite', 'sqlite3'):
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }

    if engine in ('postgres', 'postgresql'):
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'aboro_office'),
            'USER': os.getenv('DB_USER', 'aboro'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
        }

    if engine in ('mysql', 'mariadb'):
        return {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'aboro_db'),
            'USER': os.getenv('DB_USER', 'aboro_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
            'OPTIONS': {
                'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
            },
        }

    if engine in ('mssql', 'sqlserver'):
        return {
            'ENGINE': 'mssql',
            'NAME': os.getenv('DB_NAME', 'aboro_office'),
            'USER': os.getenv('DB_USER', 'aboro'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '1433'),
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
            'OPTIONS': {
                'driver': os.getenv('MSSQL_DRIVER', 'ODBC Driver 18 for SQL Server'),
            },
        }

    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


# Database default
DATABASES = {
    'default': build_database_config(),
}

# Authentication
AUTH_USER_MODEL = 'core.ABoroUser'
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Auth redirects
LOGIN_REDIRECT_URL = '/dashboard/'
LOGIN_URL = '/cloudstorage/accounts/login/'

# Installed apps
INSTALLED_APPS = [
    # Django admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ABoroOffice core apps
    'apps.core.apps.CoreConfig',
    'apps.licensing.apps.LicensingConfig',

    # Phase 2: Classroom Management (Pit-Kalendar)
    'apps.classroom.apps.ClassroomConfig',

    # Phase 3: Approvals (dokmbw_web_app)
    'apps.approvals.apps.ApprovalsConfig',

    # Phase 4: HelpDesk (tickets, knowledge, chat, admin_panel)
    'apps.helpdesk.apps.HelpDeskConfig',
    'apps.helpdesk.helpdesk_apps.tickets.apps.TicketsConfig',
    'apps.helpdesk.helpdesk_apps.knowledge.apps.KnowledgeConfig',
    'apps.helpdesk.helpdesk_apps.chat.apps.ChatConfig',
    'apps.helpdesk.helpdesk_apps.admin_panel.apps.AdminPanelConfig',
    'apps.helpdesk.helpdesk_apps.main.apps.MainConfig',
    'apps.helpdesk.helpdesk_apps.api.apps.ApiConfig',

    # Phase 5: Cloude (storage, files, sharing)
    'apps.cloude.apps.CloudeConfig',
    'apps.cloude.cloude_apps.accounts.apps.AccountsConfig',
    'apps.cloude.cloude_apps.core.apps.CoreConfig',
    'apps.cloude.cloude_apps.storage.apps.StorageConfig',
    'apps.cloude.cloude_apps.sharing.apps.SharingConfig',
    'apps.cloude.cloude_apps.plugins.apps.PluginsConfig',
    'apps.cloude.cloude_apps.api.apps.ApiConfig',

    # CRM (Business)
    'apps.crm.apps.CrmConfig',
    # Contracts (Business)
    'apps.contracts.apps.ContractsConfig',
    'apps.marketing.apps.MarketingConfig',
    'apps.erp.apps.ErpConfig',
    'apps.personnel.apps.PersonnelConfig',
    'apps.fibu.apps.FibuConfig',
    'apps.projects.apps.ProjectsConfig',
    'apps.workflows.apps.WorkflowsConfig',

    # Third-party apps (to be added as phases progress)
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'drf_spectacular',
    # 'django_extensions',
    # 'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.AppToggleMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'apps' / 'cloude' / 'cloude_apps' / 'templates',
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'apps.cloude.cloude_apps.plugins.template_loader.PluginTemplateLoader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'apps.helpdesk.helpdesk_apps.main.context_processors.branding_context',
            'apps.core.context_processors.system_settings_context',
        ],
    },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Internationalization
LANGUAGE_CODE = 'de-de'
LANGUAGES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
]
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'aboro.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Cache configuration (default: local memory, override in production)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'aboro-cache',
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_SECURE = False  # Set to True in production
SESSION_COOKIE_HTTPONLY = True

# CORS configuration (will be enhanced when frontend is added)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
]

# DRF configuration
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit

# Celery Beat Schedule (periodic tasks)
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'check-approval-deadlines': {
        'task': 'apps.approvals.celery_tasks.check_approval_deadlines',
        'schedule': crontab(minute=0),  # Every hour
    },
    'check-server-health': {
        'task': 'apps.approvals.celery_tasks.check_server_health',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}

# Email configuration (to be overridden in production)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'approvals@aboro.office')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')

# AWS Bedrock (API Key or IAM)
BEDROCK_ENABLED = os.getenv('BEDROCK_ENABLED', 'false').lower() == 'true'
BEDROCK_API_KEY = os.getenv('BEDROCK_API_KEY', '')
BEDROCK_REGION = os.getenv('BEDROCK_REGION', 'eu-central-1')
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')
BEDROCK_MAX_TOKENS = int(os.getenv('BEDROCK_MAX_TOKENS', '1024'))
BEDROCK_TEMPERATURE = float(os.getenv('BEDROCK_TEMPERATURE', '0.7'))

# Branding defaults
APP_NAME = os.getenv('APP_NAME', 'ABoroOffice')
COMPANY_NAME = os.getenv('COMPANY_NAME', 'ABoroOffice')
LOGO_URL = os.getenv('LOGO_URL', '')
APP_TITLE = os.getenv('APP_TITLE', 'ABoroOffice')

# Approvals settings
APPROVALS_ENABLED = os.getenv('APPROVALS_ENABLED', 'False') == 'True'
APPROVALS_RATE_LIMIT = {
    'count': int(os.getenv('APPROVALS_RATE_LIMIT_COUNT', 10)),
    'period': int(os.getenv('APPROVALS_RATE_LIMIT_PERIOD', 600)),
}

APPROVALS_SSH = {
    'USERNAME': os.getenv('APPROVALS_SSH_USERNAME', ''),
    'PASSWORD': os.getenv('APPROVALS_SSH_PASSWORD', ''),
    'KEY_PATH': os.getenv('APPROVALS_SSH_KEY_PATH', ''),
    'HEALTH_USERNAME': os.getenv('APPROVALS_SSH_HEALTH_USERNAME', ''),
    'HOSTS': {},
}

# Security headers (will be enabled in production)
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_SSL_REDIRECT = True

# License settings
LICENSE_CHECK_ENABLED = os.getenv('LICENSE_CHECK_ENABLED', 'True') == 'True'
LICENSE_TRIAL_DAYS = 30

# Cloude (Cloud Storage) settings
ALLOWED_FILE_EXTENSIONS = {
    # Documents
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'csv', 'json', 'xml',
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp',
    # Video
    'mp4', 'avi', 'mov', 'mkv', 'webm',
    # Audio
    'mp3', 'wav', 'flac', 'aac', 'ogg',
    # Archives
    'zip', 'rar', '7z', 'tar', 'gz', 'bz2',
}

# Helpdesk URL prefix (mount point)
HELPDESK_URL_PREFIX = '/helpdesk'
