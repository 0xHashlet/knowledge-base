from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "enterprise_rag",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["app.workers.tasks.document_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
