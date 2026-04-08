from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("aiqahub", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.imports = (
    "app.workers.ai_tasks",
    "app.workers.execution_tasks",
    "app.workers.notification_tasks",
    "app.workers.report_tasks",
    "app.workers.tasks",
)
