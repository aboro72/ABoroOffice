"""
Account and authentication URLs for HelpDesk integration.
"""

from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.helpdesk import auth_views
from apps.helpdesk.helpdesk_apps.main import views as main_views

app_name = 'helpdesk_accounts'

urlpatterns = [
    path('login/', auth_views.HelpdeskLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='helpdesk_accounts:login'), name='logout'),
    path('register/', auth_views.register, name='register'),
    path('profile/', auth_views.profile_edit, name='profile_edit'),

    # User management (reuse main app views)
    path('users/', main_views.user_management, name='user_list'),
    path('users/create/', main_views.user_create, name='user_create'),
    path('users/<int:user_id>/', auth_views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', main_views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', main_views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle-status/', main_views.user_toggle_active, name='user_toggle_active'),
]
