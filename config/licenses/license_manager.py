"""
ABoroOffice License Management System

Unterstützt die Verwaltung von Modul-Lizenzen und dynamische App-Aktivierung.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


class LicenseManager:
    """Verwaltet Lizenzen für ABoroOffice Module."""

    # Verfügbare Module
    AVAILABLE_MODULES = {
        'core': {
            'name': 'Core System',
            'description': 'Kern-Authentifizierung und Basis-System',
            'required': True,  # Immer aktiviert
        },
        'cloude': {
            'name': 'Cloude Service',
            'description': 'Cloude Cloud-Management Service',
            'required': False,
        },
        'helpdesk': {
            'name': 'HelpDesk',
            'description': 'Ticketing und Support System',
            'required': False,
        },
    }

    def __init__(self, license_file: str = 'config/licenses/active_licenses.json'):
        """Initialisiert den License Manager."""
        self.license_file = license_file
        self.active_licenses = self._load_licenses()

    def _load_licenses(self) -> Dict[str, Dict]:
        """Lädt aktive Lizenzen aus der Datei."""
        try:
            with open(self.license_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Standardmäßig: Nur Core aktiviert
            default = {
                'core': {
                    'active': True,
                    'activated_at': datetime.now().isoformat(),
                    'expires_at': None,
                }
            }
            self._save_licenses(default)
            return default

    def _save_licenses(self, licenses: Dict):
        """Speichert Lizenzen in die Datei."""
        with open(self.license_file, 'w', encoding='utf-8') as f:
            json.dump(licenses, f, indent=2, ensure_ascii=False)

    def is_module_active(self, module: str) -> bool:
        """Prüft, ob ein Modul aktiv ist."""
        if module not in self.AVAILABLE_MODULES:
            return False

        if module == 'core':  # Core ist immer aktiv
            return True

        license_info = self.active_licenses.get(module)
        if not license_info:
            return False

        if not license_info.get('active'):
            return False

        # Prüfe Ablaufdatum
        expires_at = license_info.get('expires_at')
        if expires_at:
            if datetime.fromisoformat(expires_at) < datetime.now():
                return False

        return True

    def activate_module(self, module: str, expires_at: Optional[str] = None) -> bool:
        """Aktiviert ein Modul."""
        if module not in self.AVAILABLE_MODULES:
            return False

        if module == 'core':
            return True  # Core kann nicht deaktiviert werden

        self.active_licenses[module] = {
            'active': True,
            'activated_at': datetime.now().isoformat(),
            'expires_at': expires_at,
        }
        self._save_licenses(self.active_licenses)
        return True

    def deactivate_module(self, module: str) -> bool:
        """Deaktiviert ein Modul."""
        if module == 'core':
            return False  # Core kann nicht deaktiviert werden

        if module in self.active_licenses:
            self.active_licenses[module]['active'] = False
            self._save_licenses(self.active_licenses)
            return True

        return False

    def get_active_modules(self) -> List[str]:
        """Gibt Liste aller aktiven Module zurück."""
        return [
            module for module in self.AVAILABLE_MODULES
            if self.is_module_active(module)
        ]

    def get_license_info(self, module: str) -> Optional[Dict]:
        """Gibt Lizenz-Informationen für ein Modul zurück."""
        if module not in self.AVAILABLE_MODULES:
            return None

        module_info = self.AVAILABLE_MODULES[module].copy()
        license_info = self.active_licenses.get(module, {})

        return {
            **module_info,
            **license_info,
        }

    def get_all_licenses(self) -> Dict[str, Dict]:
        """Gibt alle Lizenz-Informationen zurück."""
        result = {}
        for module in self.AVAILABLE_MODULES:
            result[module] = self.get_license_info(module)
        return result


# Globale Instanz
_license_manager = None


def get_license_manager(license_file: str = 'config/licenses/active_licenses.json') -> LicenseManager:
    """Gibt die globale License Manager Instanz zurück."""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager(license_file)
    return _license_manager
