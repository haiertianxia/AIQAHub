from pydantic import BaseModel, Field


class ExecutionCreate(BaseModel):
    project_id: str
    suite_id: str
    env_id: str
    trigger_type: str = "manual"
    trigger_source: str | None = None
    request_params: dict = Field(default_factory=dict)


class ExecutionRead(ExecutionCreate):
    id: str
    status: str = "created"
    summary: dict = Field(default_factory=dict)


class ExecutionArtifactRead(BaseModel):
    id: str
    execution_id: str
    artifact_type: str
    name: str
    storage_uri: str


class ExecutionTimelineEntry(BaseModel):
    stage: str
    status: str
    message: str
