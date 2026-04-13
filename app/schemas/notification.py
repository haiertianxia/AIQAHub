from typing import Any

from pydantic import BaseModel, Field


class NotificationPolicyRead(BaseModel):
    scope_type: str
    scope_id: str = ""
    event_type: str
    enabled: bool = True
    channels: list[str] = Field(default_factory=list)
    subject_template: str | None = None
    target: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


class NotificationSendRequest(BaseModel):
    channel: str | None = None
    subject: str | None = None
    message: str
    target: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    event_type: str | None = None
    project_id: str | None = None


class NotificationSendRead(BaseModel):
    channel: str
    provider: str
    status: str
    message: str
    target: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
