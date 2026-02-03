#!/usr/bin/env python
"""
ABoroOffice License Management CLI

Verwaltet die Aktivierung und Deaktivierung von Modulen.
"""

import sys
import argparse
from config.licenses.license_manager import get_license_manager


def list_licenses():
    """Zeigt alle verfügbaren Lizenzen an."""
    manager = get_license_manager()
    licenses = manager.get_all_licenses()

    print("\n" + "="*70)
    print("ABoroOffice - Module & Lizenzen")
    print("="*70 + "\n")

    for module, info in licenses.items():
        status = "✅ AKTIV" if info.get('active') else "❌ INAKTIV"
        required = " (ERFORDERLICH)" if info.get('required') else ""

        print(f"📦 {info['name']}{required}")
        print(f"   Status: {status}")
        print(f"   Beschreibung: {info.get('description', 'N/A')}")

        if info.get('activated_at'):
            print(f"   Aktiviert am: {info['activated_at']}")
        if info.get('expires_at'):
            print(f"   Läuft ab: {info['expires_at']}")
        print()


def activate_module(module_name):
    """Aktiviert ein Modul."""
    manager = get_license_manager()

    if module_name not in manager.AVAILABLE_MODULES:
        print(f"❌ Fehler: Modul '{module_name}' existiert nicht!")
        print(f"   Verfügbare Module: {', '.join(manager.AVAILABLE_MODULES.keys())}")
        return False

    if manager.activate_module(module_name):
        print(f"✅ Modul '{module_name}' wurde aktiviert!")
        return True
    else:
        print(f"❌ Fehler beim Aktivieren von '{module_name}'!")
        return False


def deactivate_module(module_name):
    """Deaktiviert ein Modul."""
    manager = get_license_manager()

    if module_name not in manager.AVAILABLE_MODULES:
        print(f"❌ Fehler: Modul '{module_name}' existiert nicht!")
        return False

    if manager.AVAILABLE_MODULES[module_name].get('required'):
        print(f"❌ Fehler: '{module_name}' ist erforderlich und kann nicht deaktiviert werden!")
        return False

    if manager.deactivate_module(module_name):
        print(f"✅ Modul '{module_name}' wurde deaktiviert!")
        return True
    else:
        print(f"❌ Fehler beim Deaktivieren von '{module_name}'!")
        return False


def status():
    """Zeigt den Status aller aktiven Module."""
    manager = get_license_manager()
    active = manager.get_active_modules()

    print("\n" + "="*70)
    print("Aktive Module")
    print("="*70 + "\n")

    if not active:
        print("❌ Keine Module aktiv!")
    else:
        for module in active:
            info = manager.AVAILABLE_MODULES[module]
            print(f"✅ {info['name']}")

    print()


def main():
    """Haupt-Funktion für CLI."""
    parser = argparse.ArgumentParser(
        description='ABoroOffice License Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python manage_licenses.py list              # Alle Module anzeigen
  python manage_licenses.py status            # Status aktiver Module
  python manage_licenses.py activate cloude   # Cloude aktivieren
  python manage_licenses.py deactivate cloude # Cloude deaktivieren
        """
    )

    parser.add_argument(
        'command',
        choices=['list', 'status', 'activate', 'deactivate'],
        help='Zu ausführender Befehl'
    )

    parser.add_argument(
        'module',
        nargs='?',
        help='Modul-Name (für activate/deactivate)'
    )

    args = parser.parse_args()

    if args.command == 'list':
        list_licenses()
    elif args.command == 'status':
        status()
    elif args.command == 'activate':
        if not args.module:
            print("❌ Fehler: Modul-Name erforderlich für 'activate'")
            sys.exit(1)
        activate_module(args.module)
    elif args.command == 'deactivate':
        if not args.module:
            print("❌ Fehler: Modul-Name erforderlich für 'deactivate'")
            sys.exit(1)
        deactivate_module(args.module)


if __name__ == '__main__':
    main()
