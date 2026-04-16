from sqlalchemy import JSON, String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CoverageSnapshot(Base):
    __tablename__ = "coverage_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    execution_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(64))  # jacoco, coveragepy, istanbul
    report_format: Mapped[str] = mapped_column(String(32))  # xml, json
    summary_json: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CoverageMetric(Base):
    __tablename__ = "coverage_metrics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), index=True)
    metric_type: Mapped[str] = mapped_column(String(32))  # line, branch, function, statement
    package_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    covered: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    missed: Mapped[int] = mapped_column(Integer)
    percentage: Mapped[float] = mapped_column(Float)
