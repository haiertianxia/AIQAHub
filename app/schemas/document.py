from pydantic import BaseModel, Field
from datetime import datetime


class DocumentCreate(BaseModel):
    project_id: str
    title: str
    doc_type: str  # prd, technical, api
    description: str | None = None
    content: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    content: dict | None = None
    metadata: dict | None = None
    status: str | None = None


class DocumentRead(DocumentCreate):
    id: str
    status: str
    created_by: str
    updated_by: str


class DocumentVersionCreate(BaseModel):
    document_id: str
    title: str
    content: dict = Field(default_factory=dict)
    change_description: str | None = None


class DocumentVersionRead(DocumentVersionCreate):
    id: str
    version: int
    created_by: str


class ReviewTaskCreate(BaseModel):
    document_id: str
    document_version: int
    project_id: str
    review_type: str = "hybrid"  # ai, human, hybrid
    priority: int = 2
    assignee_ids: list[str] = Field(default_factory=list)
    due_date: str | None = None
    config: dict = Field(default_factory=dict)


class ReviewTaskUpdate(BaseModel):
    status: str | None = None
    assignee_ids: list[str] | None = None
    due_date: str | None = None
    result: dict | None = None


class ReviewTaskRead(ReviewTaskCreate):
    id: str
    status: str
    result: dict | None = None
    created_by: str


class ReviewCommentCreate(BaseModel):
    review_task_id: str
    document_id: str
    parent_comment_id: str | None = None
    comment_type: str = "general"
    severity: int = 3
    line_number: int | None = None
    section_path: str | None = None
    content: str
    suggestion: str | None = None


class ReviewCommentUpdate(BaseModel):
    status: str | None = None
    content: str | None = None
    suggestion: str | None = None
    resolved_by: str | None = None


class ReviewCommentRead(ReviewCommentCreate):
    id: str
    status: str
    created_by: str
    resolved_by: str | None = None


class ReviewChecklistCreate(BaseModel):
    review_task_id: str
    doc_type: str
    item_key: str
    item_text: str
    category: str | None = None
    sort_order: int = 0


class ReviewChecklistUpdate(BaseModel):
    status: str | None = None
    comment: str | None = None
    checked_by: str | None = None


class ReviewChecklistRead(ReviewChecklistCreate):
    id: str
    status: str
    comment: str | None = None
    checked_by: str | None = None


class ReviewScoreCreate(BaseModel):
    review_task_id: str
    document_id: str
    dimension: str
    score: float
    weight: float = 1.0
    comment: str | None = None
    is_ai: bool = False


class ReviewScoreRead(ReviewScoreCreate):
    id: str
    scored_by: str


class CoverageSnapshotCreate(BaseModel):
    project_id: str
    execution_id: str | None = None
    commit_sha: str | None = None
    branch: str | None = None
    tool_name: str
    report_format: str
    summary: dict


class CoverageSnapshotRead(CoverageSnapshotCreate):
    id: str
    created_by: str | None = None


class CoverageMetricCreate(BaseModel):
    snapshot_id: str
    metric_type: str
    package_name: str | None = None
    file_path: str | None = None
    covered: int
    total: int
    missed: int
    percentage: float


class CoverageMetricRead(CoverageMetricCreate):
    id: str
