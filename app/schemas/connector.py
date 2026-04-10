from typing import Literal

from pydantic import BaseModel, Field

ConnectorStatus = Literal["created", "queued", "running", "success", "failed", "timeout", "canceled"]


class ConnectorResult(BaseModel):
    connector_type: str
    ok: bool
    status: ConnectorStatus = "created"
    message: str
    details: dict = Field(default_factory=dict)


class ConnectorRead(ConnectorResult):
    pass


class ConnectorTestPayload(BaseModel):
    payload: dict = Field(default_factory=dict)


class JenkinsCallbackPayload(BaseModel):
    execution_id: str
    job_name: str
    build_number: int
    result: str
    build_url: str | None = None
