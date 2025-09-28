from django.db import models

class SpaceWeatherData(models.Model):
    timestamp = models.DateTimeField()
    kp_index = models.FloatField()
    solar_wind_speed = models.FloatField()
    flare_class = models.CharField(max_length=10)
    risk_score = models.IntegerField()

class Subscription(models.Model):
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    threshold = models.IntegerField(default=70)
    created_at = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=50)
