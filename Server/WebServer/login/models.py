from django.db import models

# Create your models here.

class User(models.Model):
    username = models.CharField(max_length=20, primary_key=True)
    password = models.CharField(max_length=100)


class Deck(models.Model):
    deck_name = models.CharField(max_length=100)
    deck_code = models.CharField(max_length=100, primary_key=True)
    deck_desc = models.TextField()

class UserDeck(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    privilege = models.CharField(max_length=50)

    class Meta:
        unique_together = (("user", "deck"))