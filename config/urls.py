"""
ABoroOffice URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView
from apps.core.views import HomeView, DashboardView, AdminDashboardView, ApiDocsView, SystemSettingsView, PluginCardsView, BedrockTestView, UserGuideView, UserGuidePdfView, UserGuideHtmlView, HelpManualPdfView

urlpatterns = [
    # Home
    path('', HomeView.as_view(), name='home'),
    path('index/', HomeView.as_view(), name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/plugins/', PluginCardsView.as_view(), name='dashboard_plugins'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('system-settings/', SystemSettingsView.as_view(), name='system_settings'),
    path('api-docs/', ApiDocsView.as_view(), name='api_docs'),
    path('bedrock-test/', BedrockTestView.as_view(), name='bedrock_test'),
    path('user-guide/', UserGuideView.as_view(), name='user_guide'),
    path('user-guide/pdf/', UserGuidePdfView.as_view(), name='user_guide_pdf'),
    path('user-guide/html/', UserGuideHtmlView.as_view(), name='user_guide_html'),
    path('help-manual/pdf/', HelpManualPdfView.as_view(), name='help_manual_pdf'),
    path('login/', RedirectView.as_view(url='/cloudstorage/accounts/login/', permanent=False), name='login'),

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
    path('helpdesk/', include('apps.helpdesk.urls')),

    # Cloude (Phase 5)
    path('cloudstorage/', include('apps.cloude.urls')),
    path('crm/', include('apps.crm.urls')),
    path('contracts/', include('apps.contracts.urls')),
    path('marketing/', include('apps.marketing.urls')),
    path('erp/', include('apps.erp.urls')),
    path('personnel/', include('apps.personnel.urls')),
    path('fibu/', include('apps.fibu.urls')),
    path('projects/', include('apps.projects.urls')),
    path('workflows/', include('apps.workflows.urls')),
    # Cloude legacy short paths (distinct namespaces to avoid collisions)
    path(
        'storage/',
        include(('apps.cloude.cloude_apps.storage.urls', 'storage'), namespace='cloude_storage'),
    ),
    path(
        'sharing/',
        include(('apps.cloude.cloude_apps.sharing.urls', 'sharing'), namespace='cloude_sharing'),
    ),
    path(
        'accounts/',
        include(('apps.cloude.cloude_apps.accounts.urls', 'accounts'), namespace='cloude_accounts'),
    ),
    path(
        'core/',
        include(('apps.cloude.cloude_apps.core.urls', 'core'), namespace='cloude_core'),
    ),
]

# Static files configuration
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin site configuration
admin.site.site_header = "ABoroOffice Administration"
admin.site.site_title = "ABoroOffice Admin"
admin.site.index_title = "Welcome to ABoroOffice"

