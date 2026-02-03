"""
URL configuration for classroom app.
"""

from django.urls import path

app_name = 'classroom'

# Placeholder URL patterns - to be implemented
urlpatterns = [
    # Landing page
    # path('', views.LandingPageView.as_view(), name='landing'),

    # Classroom management (staff only)
    # path('classrooms/', views.ClassroomListStaffView.as_view(), name='classroom_list_staff'),
    # path('classrooms/new/', views.ClassroomCreateView.as_view(), name='classroom_create'),
    # path('classrooms/<int:pk>/edit/', views.ClassroomUpdateView.as_view(), name='classroom_update'),
    # path('classrooms/<int:pk>/delete/', views.ClassroomDeleteView.as_view(), name='classroom_delete'),

    # Deployment management (staff only)
    # path('deployments/', views.DeploymentListStaffView.as_view(), name='deployment_list_staff'),
    # path('deployments/new/', views.DeploymentCreateView.as_view(), name='deployment_create'),
    # path('deployments/<int:pk>/edit/', views.DeploymentUpdateView.as_view(), name='deployment_update'),
    # path('deployments/<int:pk>/delete/', views.DeploymentDeleteView.as_view(), name='deployment_delete'),
]
