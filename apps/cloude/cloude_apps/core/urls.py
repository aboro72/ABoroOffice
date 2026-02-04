"""
URL configuration for Core app.
"""

from django.urls import path
from apps.cloude.cloude_apps.core import views
from apps.cloude.cloude_apps.api.views import PluginDiscoverView

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('landing/', views.landing, name='landing'),
    path('activity/', views.activity_log, name='activity_log'),
    path('search/', views.search, name='search'),
    path('settings/', views.settings, name='settings'),
    path('plugins/discover/', PluginDiscoverView.as_view(), name='plugin_discover'),
    path('help/', views.help_page, name='help'),
    path('help/developer/', views.help_developer, name='help_developer'),
]
