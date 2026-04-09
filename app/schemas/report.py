from pydantic import BaseModel, Field


class ReportSummary(BaseModel):
    execution_id: str
    summary: dict = Field(default_factory=dict)
    artifacts: list[dict] = Field(default_factory=list)
    tasks: list[dict] = Field(default_factory=list)
    task_count: int = 0


class ReportIndexItem(ReportSummary):
    status: str = "unknown"
