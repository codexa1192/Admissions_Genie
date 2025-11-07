"""
Celery worker configuration for background task processing.
Handles async document processing to prevent UI blocking.
"""

from celery import Celery
from config.settings import Config

# Initialize Celery
celery_app = Celery(
    'admissions_genie',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=['tasks.admission_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Chicago',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

if __name__ == '__main__':
    celery_app.start()
