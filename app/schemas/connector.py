from pydantic import BaseModel, Field


class ConnectorRead(BaseModel):
    connector_type: str
    ok: bool
    message: str
    details: dict = Field(default_factory=dict)


class ConnectorTestPayload(BaseModel):
    payload: dict = Field(default_factory=dict)
