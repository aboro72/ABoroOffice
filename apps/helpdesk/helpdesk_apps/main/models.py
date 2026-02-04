from django.db import models
from django.conf import settings


class GameHighscore(models.Model):
    """Highscore entries for the secret Retro Runner game"""

    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_scores'
    )
    score = models.IntegerField(default=0)
    level_reached = models.IntegerField(default=1)
    coins_collected = models.IntegerField(default=0)
    time_played = models.IntegerField(default=0, help_text="Time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', '-created_at']
        verbose_name = 'Game Highscore'
        verbose_name_plural = 'Game Highscores'

    def __str__(self):
        player_name = self.player.full_name if hasattr(self.player, 'full_name') else f"{self.player.first_name} {self.player.last_name}"
        return f"{player_name} - Score: {self.score}"

    @classmethod
    def get_top_scores(cls, limit=10):
        """Get top scores with player info"""
        return cls.objects.select_related('player').all()[:limit]

    @classmethod
    def get_player_best_score(cls, player):
        """Get player's best score"""
        return cls.objects.filter(player=player).first()


class VirusKongHighscore(models.Model):
    """Highscore entries for Virus Kong game"""

    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='viruskong_scores'
    )
    score = models.IntegerField(default=0)
    level_reached = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', '-created_at']
        verbose_name = 'Virus Kong Highscore'
        verbose_name_plural = 'Virus Kong Highscores'

    def __str__(self):
        player_name = self.player.full_name if hasattr(self.player, 'full_name') else f"{self.player.first_name} {self.player.last_name}"
        return f"{player_name} - Score: {self.score}"

    @classmethod
    def get_top_scores(cls, limit=10):
        """Get top scores with player info"""
        return cls.objects.select_related('player').all()[:limit]

    @classmethod
    def get_player_best_score(cls, player):
        """Get player's best score"""
        return cls.objects.filter(player=player).first()
