"""
Django app config for Claude Code Widget plugin.
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ClaudeCodeConfig(AppConfig):
    """Configuration for Claude Code Widget plugin"""

    name = 'claude_code'
    verbose_name = 'Claude Code Widget Plugin'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """
        Called when plugin is activated.
        Registers the Claude Code widget with the hook system.
        """
        logger.info("Initializing Claude Code Widget Plugin")

        try:
            from plugins.hooks import hook_registry, UI_DASHBOARD_WIDGET
            from claude_code.widget import ClaudeCodeWidgetProvider

            # Register the dashboard widget
            hook_registry.register(
                UI_DASHBOARD_WIDGET,
                ClaudeCodeWidgetProvider,
                priority=5,  # High priority to show at top
            )

            logger.info("Claude Code Widget registered successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Claude Code Widget Plugin: {e}")
            raise
