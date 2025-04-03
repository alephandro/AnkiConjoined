from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    def __str__(self):
        return self.user.username


class Deck(models.Model):
    deck_name = models.CharField(max_length=100)
    deck_code = models.CharField(max_length=100, primary_key=True)
    deck_desc = models.TextField()

    def __str__(self):
        return self.deck_name


class UserDeck(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    privilege = models.CharField(max_length=50)

    class Meta:
        unique_together = (("user", "deck"))