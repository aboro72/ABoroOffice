from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('settings/', views.admin_settings, name='admin_settings'),
    path('license/', views.manage_license, name='manage_license'),
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle/', views.user_toggle_active, name='user_toggle_active'),
    path('debug-widget/', views.debug_widget_codes, name='debug_widget'),
    # Easter Egg - Secret Games
    path('secret-retro-game/', views.retro_game, name='retro_game'),
    path('game/save-score/', views.game_save_score, name='game_save_score'),
    path('game/highscores/', views.game_get_highscores, name='game_highscores'),
    # Virus Kong
    path('virus-kong/', views.virus_kong_game, name='virus_kong'),
    path('game/save-score-viruskong/', views.game_save_score_viruskong, name='game_save_score_viruskong'),
    path('game/highscores-viruskong/', views.game_get_highscores_viruskong, name='game_highscores_viruskong'),
]
