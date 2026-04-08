from app.workers.celery_app import celery_app


@celery_app.task(name="aiqahub.notification.send")
def send_notification(message: str) -> dict[str, str]:
    return {"sent": "true", "message": message}

