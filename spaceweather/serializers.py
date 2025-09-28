from rest_framework import serializers
from .models import SpaceWeatherData, Subscription
from rest_framework.validators import UniqueValidator

class SpaceWeatherSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceWeatherData
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=Subscription.objects.all())]
    )
    class Meta:
        model = Subscription
        fields = '__all__'
