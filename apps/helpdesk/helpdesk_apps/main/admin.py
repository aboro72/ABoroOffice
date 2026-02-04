from django.contrib import admin
from .models import GameHighscore, VirusKongHighscore


@admin.register(GameHighscore)
class GameHighscoreAdmin(admin.ModelAdmin):
    list_display = ['player', 'score', 'level_reached', 'coins_collected', 'time_played', 'created_at']
    list_filter = ['level_reached', 'created_at']
    search_fields = ['player__username', 'player__first_name', 'player__last_name']
    readonly_fields = ['created_at']
    ordering = ['-score', '-created_at']

    def has_add_permission(self, request):
        # Prevent manual creation of highscores in admin
        return False


@admin.register(VirusKongHighscore)
class VirusKongHighscoreAdmin(admin.ModelAdmin):
    list_display = ['player', 'score', 'level_reached', 'created_at']
    list_filter = ['level_reached', 'created_at']
    search_fields = ['player__username', 'player__first_name', 'player__last_name']
    readonly_fields = ['created_at']
    ordering = ['-score', '-created_at']

    def has_add_permission(self, request):
        # Prevent manual creation of highscores in admin
        return False
