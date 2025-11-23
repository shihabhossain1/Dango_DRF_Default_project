import os
from decouple import config
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_aggregator.settings')

app = Celery('travel_aggregator')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
