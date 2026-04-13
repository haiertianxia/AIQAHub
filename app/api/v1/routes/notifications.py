from fastapi import APIRouter, Query

from app.schemas.notification import NotificationSendRead, NotificationSendRequest
from app.services.notification_service import NotificationService

router = APIRouter()
service = NotificationService()


@router.post("/test", response_model=NotificationSendRead)
def test_notification(
    payload: NotificationSendRequest,
    environment: str | None = Query(default=None),
) -> NotificationSendRead:
    return service.send(payload, environment=environment)
