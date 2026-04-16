from pydantic import BaseModel, Field


class QualityRuleCreate(BaseModel):
    project_id: str
    name: str
    rule_type: str  # success_rate, task_count, critical_tasks, doc_review, doc_score, coverage, coverage_delta
    enabled: bool = True
    config: dict = Field(default_factory=dict)


class QualityRuleUpdate(BaseModel):
    name: str | None = None
    rule_type: str | None = None
    enabled: bool | None = None
    config: dict | None = None


class QualityRuleRead(QualityRuleCreate):
    id: str
    version: int = 1


class GateEvaluateRequest(BaseModel):
    execution_id: str | None = None
    document_id: str | None = None
    coverage_snapshot_id: str | None = None
    project_id: str | None = None


class GateCheckResult(BaseModel):
    rule_id: str
    rule_type: str
    rule_name: str
    passed: bool
    actual_value: float | str | None = None
    threshold_value: float | str | None = None
    message: str | None = None


class GateResult(BaseModel):
    evaluation_id: str = "demo"
    execution_id: str | None = None
    document_id: str | None = None
    coverage_snapshot_id: str | None = None
    project_id: str | None = None
    result: str = "WARN"  # PASS, WARN, FAIL
    overall_score: int = 0
    reason: str = "not evaluated"
    checks: list[GateCheckResult] = Field(default_factory=list)
    task_count: int = 0
    failed_tasks: int = 0
    task_threshold: int = 0
    completion_source: str | None = None

    def is_blocking(self) -> bool:
        return self.result == "FAIL"


class QualityRuleRevisionRead(BaseModel):
    id: str
    rule_id: str
    version: int
    action: str
    before_json: dict | None = None
    after_json: dict | None = None

    def governance_source_id(self) -> str:
        return self.id


# Predefined rule templates
class RuleTemplate(BaseModel):
    name: str
    rule_type: str
    description: str
    default_config: dict


DOCUMENT_REVIEW_RULE_TEMPLATES: list[RuleTemplate] = [
    RuleTemplate(
        name="Document Must Be Approved",
        rule_type="doc_review",
        description="Require document to be in APPROVED status",
        default_config={"required_status": "APPROVED"},
    ),
    RuleTemplate(
        name="Minimum Document Score",
        rule_type="doc_score",
        description="Require document to meet minimum quality score",
        default_config={"min_score": 80, "score_dimension": "overall"},
    ),
]

COVERAGE_RULE_TEMPLATES: list[RuleTemplate] = [
    RuleTemplate(
        name="Minimum Line Coverage",
        rule_type="coverage",
        description="Require minimum line coverage percentage",
        default_config={"min_coverage": 80, "metric_type": "line"},
    ),
    RuleTemplate(
        name="Minimum Branch Coverage",
        rule_type="coverage",
        description="Require minimum branch coverage percentage",
        default_config={"min_coverage": 70, "metric_type": "branch"},
    ),
    RuleTemplate(
        name="Coverage Drop Protection",
        rule_type="coverage_delta",
        description="Prevent coverage from dropping more than threshold",
        default_config={"max_drop": 2, "metric_type": "line"},
    ),
]

TEST_RULE_TEMPLATES: list[RuleTemplate] = [
    RuleTemplate(
        name="Minimum Success Rate",
        rule_type="success_rate",
        description="Require minimum test success rate",
        default_config={"min_success_rate": 95},
    ),
    RuleTemplate(
        name="Critical Tasks Must Pass",
        rule_type="critical_tasks",
        description="Specified critical tasks must all pass",
        default_config={"critical_task_keys": []},
    ),
    RuleTemplate(
        name="Minimum Task Count",
        rule_type="task_count",
        description="Require minimum number of tasks to run",
        default_config={"min_task_count": 3},
    ),
]

ALL_RULE_TEMPLATES: list[RuleTemplate] = (
    DOCUMENT_REVIEW_RULE_TEMPLATES + COVERAGE_RULE_TEMPLATES + TEST_RULE_TEMPLATES
)
