"""
URL Configuration for Approvals App
"""

from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    # List & Detail Views
    path('', views.ApprovalListView.as_view(), name='list'),
    path('<uuid:token>/', views.ApprovalDetailView.as_view(), name='detail'),
    path('approval/<int:pk>/', views.ApprovalDetailView.as_view(), name='detail-pk'),

    # Workflow Actions
    path('<uuid:token>/approve/', views.ApprovalApproveView.as_view(), name='approve-token'),
    path('approval/<int:pk>/approve/', views.ApprovalApproveView.as_view(), name='approve'),
    path('approval/<int:pk>/reject/', views.ApprovalRejectView.as_view(), name='reject'),

    # Health & Status
    path('health/', views.ServerHealthCheckView.as_view(), name='health-list'),
    path('health/<str:server_name>/', views.ServerHealthCheckView.as_view(), name='health-detail'),
    path('schedule/', views.RatingScheduleStatusView.as_view(), name='schedule-list'),
    path('schedule/<int:schedule_id>/', views.RatingScheduleStatusView.as_view(), name='schedule-detail'),

    # Statistics
    path('statistics/', views.ApprovalStatisticsView.as_view(), name='statistics'),
]
