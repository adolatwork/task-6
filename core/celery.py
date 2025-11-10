import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-failed-tasks': {
        'task': 'tasks.check_failed_tasks',
        'schedule': crontab(minute=0),
    },
    'cleanup-old-tasks': {
        'task': 'tasks.cleanup_old_tasks',
        'schedule': crontab(minute='*/30'),
    },
}


@app.task(bind=True)
def debug_task(self):
    """Debug task - Celery ishlayotganini tekshirish"""
    print(f'Request: {self.request!r}')
