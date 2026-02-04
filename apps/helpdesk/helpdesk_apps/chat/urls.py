from django.urls import path
from . import views
from . import agent_views

app_name = 'chat'

urlpatterns = [
    # Public endpoints for chat widget
    path('widget/', views.chat_widget, name='widget'),
    path('widget-data/', views.widget_data, name='widget_data'),
    path('widget.js', views.widget_script, name='widget_script'),
    path('debug-widget.js', views.debug_widget_script, name='debug_widget_script'),
    path('widget-test/', views.widget_test, name='widget_test'),
    path('api/start/', views.start_chat, name='start_chat'),
    path('api/send/', views.send_message, name='send_message'),
    path('api/messages/<str:session_id>/', views.get_messages, name='get_messages'),
    
    # NEW Agent Dashboard URLs
    path('agent/', agent_views.chat_dashboard, name='agent_dashboard_new'),
    path('agent/session/<str:session_id>/', agent_views.chat_session_detail, name='agent_session_detail'),
    path('agent/take/<str:session_id>/', agent_views.take_chat_session, name='take_session'),
    path('agent/send/<str:session_id>/', agent_views.send_agent_message, name='send_agent_message'),
    path('agent/close/<str:session_id>/', agent_views.close_chat_session, name='close_session'),
    path('agent/transfer-ai/<str:session_id>/', agent_views.transfer_to_ai, name='transfer_to_ai'),
    path('agent/messages/<str:session_id>/', agent_views.get_session_messages, name='get_session_messages'),
    path('agent/faq-template/<str:session_id>/', agent_views.use_faq_template, name='use_faq_template'),
    
    # Legacy Agent endpoints (keep for compatibility)
    path('dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/take/<str:session_id>/', views.agent_take_chat, name='agent_take_chat'),
    path('api/send/<str:session_id>/', views.agent_send_message, name='agent_send_message'),
    path('api/end/<str:session_id>/', views.end_chat, name='end_chat'),
    path('session/<str:session_id>/', views.chat_detail, name='chat_detail'),
]