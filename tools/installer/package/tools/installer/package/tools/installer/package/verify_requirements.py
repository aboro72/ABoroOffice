#!/usr/bin/env python
"""
Verify ABoroOffice Requirements Installation

This script checks that all required packages are correctly installed
and compatible with each other.

Usage:
    python verify_requirements.py
"""

import sys
import subprocess
from importlib import import_module
from packaging import version as pkg_version

# Core packages to verify
CORE_PACKAGES = [
    'django',
    'rest_framework',
    'channels',
    'celery',
    'redis',
    'cryptography',
]

# Version checks
EXPECTED_VERSIONS = {
    'django': ('6.0', '6.1.0'),  # Django 6.0.x (Latest)
    'celery': ('5.6', '5.9.99'),
    'redis': ('7.0', '8.0.0'),
}

# Platform-specific packages
PLATFORM_PACKAGES = {
    'windows': ['pydantic >= 1.10.0, < 2.0.0'],
    'linux': ['pydantic >= 2.5.0, < 3.0.0'],
}

def check_package(package_name, import_name=None):
    """Check if package is installed and importable."""
    if import_name is None:
        import_name = package_name.replace('-', '_')

    try:
        mod = import_module(import_name)
        version_str = getattr(mod, '__version__', 'unknown')
        return True, version_str
    except ImportError:
        return False, None

def check_version(package_name, installed_version, expected_min, expected_max):
    """Check if installed version is within expected range."""
    try:
        installed = pkg_version.parse(installed_version)
        min_ver = pkg_version.parse(expected_min)
        max_ver = pkg_version.parse(expected_max)

        if min_ver <= installed < max_ver:
            return True, f"{installed_version} ✓"
        else:
            return False, f"{installed_version} (expected {expected_min} - {expected_max})"
    except Exception as e:
        return False, f"Error checking version: {e}"

def main():
    """Run verification checks."""
    print("=" * 60)
    print("ABoroOffice Requirements Verification")
    print("=" * 60)

    # Check Python version
    py_version = sys.version_info
    print(f"\n✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")

    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        print("  ⚠ Warning: Python 3.8+ recommended")
        return 1

    # Check core packages
    print("\nCore Packages:")
    print("-" * 60)
    all_ok = True

    for pkg in CORE_PACKAGES:
        installed, version = check_package(pkg)

        if installed:
            # Check version if we have expectations
            if pkg in EXPECTED_VERSIONS:
                min_v, max_v = EXPECTED_VERSIONS[pkg]
                ver_ok, ver_msg = check_version(pkg, version, min_v, max_v)
                status = "✓" if ver_ok else "✗"
                print(f"  {status} {pkg:20} {ver_msg}")
                if not ver_ok:
                    all_ok = False
            else:
                print(f"  ✓ {pkg:20} {version}")
        else:
            print(f"  ✗ {pkg:20} NOT INSTALLED")
            all_ok = False

    # Check platform-specific packages
    print("\nPlatform-Specific Packages:")
    print("-" * 60)

    if sys.platform == 'win32':
        print("  Detected: Windows")
        # Check for pydantic v1
        installed, version = check_package('pydantic', 'pydantic')
        if installed:
            try:
                ver = pkg_version.parse(version)
                if ver.major == 1:
                    print(f"  ✓ pydantic {version} (v1.x - correct for Windows)")
                else:
                    print(f"  ⚠ pydantic {version} (v{ver.major}.x - check if pre-built wheels available)")
            except:
                print(f"  ✓ pydantic {version}")
    else:
        print("  Detected: Linux/Unix")
        # Check for pydantic v2
        installed, version = check_package('pydantic', 'pydantic')
        if installed:
            try:
                ver = pkg_version.parse(version)
                if ver.major == 2:
                    print(f"  ✓ pydantic {version} (v2.x - correct for Linux)")
                else:
                    print(f"  ⚠ pydantic {version} (v{ver.major}.x - check compatibility)")
            except:
                print(f"  ✓ pydantic {version}")

    # Check Django apps
    print("\nDjango Apps:")
    print("-" * 60)
    django_apps = [
        ('rest_framework', 'djangorestframework'),
        ('channels', 'channels'),
        ('celery', 'celery'),
        ('guardian', 'django-guardian'),
        ('jazzmin', 'django-jazzmin'),
    ]

    for import_name, display_name in django_apps:
        installed, version = check_package(import_name, import_name)
        status = "✓" if installed else "✗"
        ver_str = f" {version}" if version else " NOT INSTALLED"
        print(f"  {status} {display_name:25} {ver_str}")
        if not installed:
            all_ok = False

    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ All requirements verified successfully!")
        print("  Ready for development/deployment")
        return 0
    else:
        print("✗ Some requirements are missing or incorrect")
        print("  Run: pip install -r requirements-windows.txt  (Windows)")
        print("  Or:  pip install -r requirements-linux.txt    (Linux)")
        return 1

if __name__ == '__main__':
    sys.exit(main())
