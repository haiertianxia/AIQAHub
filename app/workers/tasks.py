from app.workers.celery_app import celery_app


@celery_app.task(name="aiqahub.health_check")
def health_check_task() -> dict[str, str]:
    return {"status": "ok"}

