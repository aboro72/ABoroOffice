"""
URLs for update management
"""

from django.urls import path
from .update_views import (
    check_updates_view,
    install_updates_view,
    update_history_view,
    force_check_updates,
    UpdateNotificationListView,
    UpdateNotificationDetailView
)

app_name = 'updates'

urlpatterns = [
    # Check for updates
    path('check/', check_updates_view, name='check'),
    path('check/force/', force_check_updates, name='force_check'),

    # Install updates
    path('install/', install_updates_view, name='install'),

    # History and details
    path('history/', update_history_view, name='history'),
    path('notifications/', UpdateNotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/', UpdateNotificationDetailView.as_view(), name='notification_detail'),
]
