"""
Claude Code Dashboard Widget.

Provides access to Claude Code for all users.
Users with aboro72_* prefix can use shared root credentials.
"""

import re
from typing import Dict, Any
from plugins.widgets import DashboardWidgetProvider
import logging

logger = logging.getLogger(__name__)


class ClaudeCodeWidgetProvider(DashboardWidgetProvider):
    """Dashboard widget providing Claude Code access for all users."""

    widget_id = "claude_code_widget"
    widget_name = "Claude Code"
    widget_icon = "bi-robot"
    widget_size = "medium"
    widget_order = 5  # Show near top

    # Pattern for users who can use shared credentials
    SHARED_USER_PATTERN = r'^aboro72_.*$'

    def get_plugin_settings(self) -> Dict[str, Any]:
        """Get settings from the database."""
        try:
            from plugins.models import Plugin
            plugin = Plugin.objects.get(slug='claude-code')
            return plugin.settings or {}
        except Exception as e:
            logger.warning(f"Could not load Claude Code settings: {e}")
            return {}

    def is_shared_user(self, username: str) -> bool:
        """Check if user matches the shared credentials pattern (aboro72_*)."""
        return bool(re.match(self.SHARED_USER_PATTERN, username))

    def is_visible(self, request) -> bool:
        """
        Check if widget should be shown to current user.
        Shows to all users by default, or only aboro72_* users if configured.
        """
        if not request.user.is_authenticated:
            return False

        settings = self.get_plugin_settings()
        visibility = settings.get('show_for_all_users', 'all')

        if visibility == 'aboro72_only':
            return self.is_shared_user(request.user.username)

        return True

    def get_context(self, request) -> Dict[str, Any]:
        """Get context data for the widget."""
        settings = self.get_plugin_settings()
        username = request.user.username
        is_shared = self.is_shared_user(username)

        claude_code_url = settings.get('claude_code_url', 'https://claude.ai/claude-code')
        shared_info = settings.get('shared_credentials_info', '')

        return {
            'username': username,
            'is_shared_user': is_shared,
            'claude_code_url': claude_code_url,
            'shared_credentials_info': shared_info if is_shared else None,
            'features': [
                'KI-gestuetzte Code-Assistenz',
                'Terminal-Integration',
                'Multi-Datei-Bearbeitung',
                'Git-Integration',
            ],
        }

    def get_template_name(self) -> str:
        return 'claude_code/widget.html'
