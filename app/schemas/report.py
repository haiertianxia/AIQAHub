from pydantic import BaseModel, Field


class ReportSummary(BaseModel):
    execution_id: str
    status: str = "unknown"
    summary: dict = Field(default_factory=dict)
    artifacts: list[dict] = Field(default_factory=list)
    tasks: list[dict] = Field(default_factory=list)
    task_count: int = 0
    completion_source: str | None = None
    completed_at: str | None = None
    started_at: str | None = None


class ReportIndexItem(ReportSummary):
    pass
