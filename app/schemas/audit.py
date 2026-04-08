from pydantic import BaseModel, Field


class AuditLogRead(BaseModel):
    id: str
    actor_id: str | None = None
    action: str
    target_type: str
    target_id: str
    request_json: dict = Field(default_factory=dict)
    response_json: dict = Field(default_factory=dict)

