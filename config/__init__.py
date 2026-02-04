"""
ABoroOffice Konfiguration

Initialisiert das Lizenzierungssystem, Celery und die Modul-Verwaltung.
"""

from config.licenses.license_manager import get_license_manager
from config.celery import app as celery_app

# Initialisiere den License Manager beim Start
license_manager = get_license_manager()

__all__ = ['license_manager', 'celery_app']
