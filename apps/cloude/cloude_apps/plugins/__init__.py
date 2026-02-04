"""
CloudService Plugin System

A modular plugin system that allows administrators to extend CloudService
with new file preview types, storage backends, and other features.

Usage:
    - Upload plugins as ZIP files via Django Admin
    - Activate/deactivate without server restart (hot-loading)
    - Plugin hooks system for extensibility
"""

default_app_config = 'apps.cloude.cloude_apps.plugins.apps.PluginsConfig'
