"""
Celery configuration for AutoParts Kenya.
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoparts_kenya.settings')

app = Celery('autoparts_kenya')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule (for periodic tasks)
app.conf.beat_schedule = {
    # Example: Check for low stock every hour
    'check-low-stock-every-hour': {
        'task': 'products.tasks.check_low_stock',
        'schedule': crontab(minute=0),  # Every hour
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
