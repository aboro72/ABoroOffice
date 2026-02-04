"""
Signal handlers for admin panel models
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import SystemSettings

try:
    from apps.helpdesk.helpdesk_apps.chat.models import ChatSettings
except ImportError:
    ChatSettings = None


@receiver(post_save, sender=SystemSettings)
def invalidate_system_settings_cache(sender, instance, **kwargs):
    """
    Invalidate system settings cache when settings are updated.
    This ensures that the website reflects new settings immediately.
    """
    cache_key = 'admin_system_settings'
    cache.delete(cache_key)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"System settings cache cleared: {cache_key}")


# Only register ChatSettings signal if it exists
if ChatSettings:
    @receiver(post_save, sender=ChatSettings)
    def invalidate_chat_settings_cache(sender, instance, **kwargs):
        """
        Invalidate chat settings cache when settings are updated.
        """
        cache_key = 'chat_settings'
        cache.delete(cache_key)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Chat settings cache cleared: {cache_key}")
