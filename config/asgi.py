"""
ASGI config for ABoroOffice project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Use development settings by default
# Override with environment variable for production:
# export DJANGO_SETTINGS_MODULE=config.settings.production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

django_asgi_app = get_asgi_application()

# WebSocket routing (to be configured in Phase 5 for Cloude)
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # WebSocket routing will be added when Cloude is integrated
    # "websocket": AuthMiddlewareStack(
    #     URLRouter([
    #         re_path(r'ws/cloude/(?P<room_name>\w+)/$', ...),
    #     ])
    # ),
})
