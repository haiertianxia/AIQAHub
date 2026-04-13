from typing import Any

from pydantic import BaseModel, Field


class NotificationSendRequest(BaseModel):
    channel: str | None = None
    subject: str | None = None
    message: str
    target: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationSendRead(BaseModel):
    channel: str
    provider: str
    status: str
    message: str
    target: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
