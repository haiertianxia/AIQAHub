from pydantic import BaseModel, Field


class ReportSummary(BaseModel):
    execution_id: str
    summary: dict = Field(default_factory=dict)
    artifacts: list[dict] = Field(default_factory=list)


class ReportIndexItem(ReportSummary):
    status: str = "unknown"
