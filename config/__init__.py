"""
ABoroOffice Konfiguration

Initialisiert das Lizenzierungssystem und die Modul-Verwaltung.
"""

from config.licenses.license_manager import get_license_manager

# Initialisiere den License Manager beim Start
license_manager = get_license_manager()

__all__ = ['license_manager']
