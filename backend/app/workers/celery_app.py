from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "crm_worker",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "poll-email-every-minute": {
        "task": "poll_email_channels",
        "schedule": 60.0,
    },
}