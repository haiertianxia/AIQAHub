from app.schemas.notification import NotificationSendRequest
from app.workers.celery_app import celery_app
from app.services.notification_service import NotificationService


@celery_app.task(name="aiqahub.notification.send")
def send_notification(
    message: str,
    *,
    subject: str | None = None,
    channel: str | None = None,
    target: str | None = None,
    environment: str | None = None,
    metadata: dict | None = None,
) -> dict[str, object]:
    service = NotificationService()
    result = service.send(
        NotificationSendRequest(
            channel=channel,
            subject=subject,
            message=message,
            target=target,
            metadata=metadata or {},
        ),
        environment=environment,
    )
    return result.model_dump()
