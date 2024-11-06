import uuid

from django.db import models

# Create your models here.
from rest_framework.authtoken.admin import User

from main.models import Log


class Level:
    pass


class Customer(User):
    # phone = models.CharField(max_length=255, null=True)
    image = models.ImageField(null=True)

    class Meta:
        db_table = 'customer'


class Badges(Log):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_badges', null=True)
    level = models.CharField(max_length=255, null=True)
    active = models.CharField(default=True)

    class Meta:
        db_table = 'badges'


class Teams(Log):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='teams', null=True)
    name = models.CharField(max_length=255, null=True)
    typ = models.CharField(max_length=255, null=True)
    token = models.UUIDField(null=True,)

    class Meta:
        db_table = 'teams'


class Players(Log):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_teams', null=True)
    team = models.ForeignKey(Teams, on_delete=models.CASCADE, related_name='team_players', null=True)

    class Meta:
        db_table = 'teams_players'


class Activity(Log):
    creator = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_activity', null=True)
    sport = models.CharField(max_length=255, null=True)
    date = models.DateField(null=True)
    location = models.CharField(max_length=255)
    public = models.BooleanField(default=True)

    class Meta:
        db_table = 'customer_activity'
