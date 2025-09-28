
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sw_server.settings')
app = Celery('sw_server')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    'fetch-every-1-minutes': {
        'task': 'spaceweather.tasks.fetch_space_weather',
        'schedule': crontab(minute='*/5'),
    },
}
