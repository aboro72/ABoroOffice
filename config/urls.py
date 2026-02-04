"""
ABoroOffice URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from apps.core.views import HomeView

urlpatterns = [
    # Home
    path('', HomeView.as_view(), name='home'),

    # Admin interface
    path('admin/', admin.site.urls),

    # Core API and auth (to be implemented)
    # path('api/auth/', include('rest_framework.urls')),
    # path('api/auth/token/', views.obtain_auth_token),

    # App-specific URLs (will be added as phases progress)
    # Classroom / Pit-Kalendar (Phase 2) ✅ INTEGRATED
    path('classroom/', include('apps.classroom.urls')),

    # Approvals (Phase 3) ✅ INTEGRATED
    path('approvals/', include('apps.approvals.urls')),

    # HelpDesk Suite (Phase 4)
    # path('helpdesk/', include('apps.helpdesk_suite.urls')),

    # Cloude (Phase 5)
    # path('cloude/', include('apps.cloude.urls')),
]

# Static files configuration
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin site configuration
admin.site.site_header = "ABoroOffice Administration"
admin.site.site_title = "ABoroOffice Admin"
admin.site.index_title = "Welcome to ABoroOffice"
