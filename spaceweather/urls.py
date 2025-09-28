from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from spaceweather.views import *
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register('spacewx', SpaceWeatherViewSet, basename='spacewx')
router.register('subscribe', SubscriptionViewSet, basename='subscribe')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('story/',generate_story)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)