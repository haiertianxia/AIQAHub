from pydantic import BaseModel, Field


class QualityRuleCreate(BaseModel):
    project_id: str
    name: str
    rule_type: str
    enabled: bool = True
    config: dict = Field(default_factory=dict)


class QualityRuleUpdate(BaseModel):
    name: str | None = None
    rule_type: str | None = None
    enabled: bool | None = None
    config: dict | None = None


class QualityRuleRead(QualityRuleCreate):
    id: str


class GateEvaluateRequest(BaseModel):
    execution_id: str


class GateResult(BaseModel):
    execution_id: str = "demo"
    result: str = "WARN"
    score: int = 0
    reason: str = "not evaluated"
    task_count: int = 0
    failed_tasks: int = 0
    task_threshold: int = 0
