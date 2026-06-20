"""Celery app factory."""

from celery import Celery
from app.core.config import settings

celery_app = Celery("interview_agent", broker=settings.REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_backend=settings.REDIS_URL,
    task_soft_time_limit=120,
    task_time_limit=300,
)

celery_app.autodiscover_tasks(["app.tasks"])
