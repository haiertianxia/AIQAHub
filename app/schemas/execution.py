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
    completion_source: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class ExecutionArtifactRead(BaseModel):
    id: str
    execution_id: str
    artifact_type: str
    name: str
    storage_uri: str


class ExecutionTaskRead(BaseModel):
    id: str
    execution_id: str
    task_key: str
    task_name: str
    status: str
    input: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)
    error_message: str | None = None


class ExecutionTimelineEntry(BaseModel):
    stage: str
    status: str
    message: str


class ExecutionDispatchRead(BaseModel):
    execution_id: str
    status: str
    task_id: str
    summary: dict = Field(default_factory=dict)
