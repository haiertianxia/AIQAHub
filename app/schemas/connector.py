from pydantic import BaseModel, Field


class ConnectorRead(BaseModel):
    connector_type: str
    ok: bool
    message: str
    details: dict = Field(default_factory=dict)


class ConnectorTestPayload(BaseModel):
    payload: dict = Field(default_factory=dict)


class JenkinsCallbackPayload(BaseModel):
    execution_id: str
    job_name: str
    build_number: int
    result: str
    build_url: str | None = None
