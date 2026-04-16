from sqlalchemy import JSON, String, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    document_version: Mapped[int] = mapped_column(Integer)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    review_type: Mapped[str] = mapped_column(String(32))  # ai, human, hybrid
    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1-5
    assignee_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str] = mapped_column(String(64))


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    review_task_id: Mapped[str] = mapped_column(String(64), index=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    parent_comment_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    comment_type: Mapped[str] = mapped_column(String(32), default="general")  # general, issue, suggestion, question
    status: Mapped[str] = mapped_column(String(32), default="open")  # open, resolved, dismissed
    severity: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(64))
    resolved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ReviewChecklist(Base):
    __tablename__ = "review_checklists"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    review_task_id: Mapped[str] = mapped_column(String(64), index=True)
    doc_type: Mapped[str] = mapped_column(String(64))  # prd, technical, api
    item_key: Mapped[str] = mapped_column(String(128))
    item_text: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, passed, failed, na
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ReviewScore(Base):
    __tablename__ = "review_scores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    review_task_id: Mapped[str] = mapped_column(String(64), index=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    dimension: Mapped[str] = mapped_column(String(64))  # completeness, clarity, consistency, feasibility
    score: Mapped[float] = mapped_column(Float)  # 0-100
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    scored_by: Mapped[str] = mapped_column(String(64))
    is_ai: Mapped[bool] = mapped_column(default=False)
