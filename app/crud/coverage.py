from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.crud.base import Repository
from app.models.coverage import CoverageSnapshot, CoverageMetric


class CoverageSnapshotRepository(Repository[CoverageSnapshot]):
    def __init__(self) -> None:
        super().__init__(CoverageSnapshot)

    def list_by_project(self, db: Session, project_id: str, limit: int = 100) -> list[CoverageSnapshot]:
        statement = select(CoverageSnapshot).where(
            CoverageSnapshot.project_id == project_id
        ).order_by(desc(CoverageSnapshot.id)).limit(limit)
        return list(db.scalars(statement).all())

    def list_by_branch(self, db: Session, project_id: str, branch: str, limit: int = 100) -> list[CoverageSnapshot]:
        statement = select(CoverageSnapshot).where(
            CoverageSnapshot.project_id == project_id,
            CoverageSnapshot.branch == branch
        ).order_by(desc(CoverageSnapshot.id)).limit(limit)
        return list(db.scalars(statement).all())

    def get_latest_by_commit(self, db: Session, project_id: str, commit_sha: str) -> CoverageSnapshot | None:
        statement = select(CoverageSnapshot).where(
            CoverageSnapshot.project_id == project_id,
            CoverageSnapshot.commit_sha == commit_sha
        ).order_by(desc(CoverageSnapshot.id)).limit(1)
        return db.scalars(statement).first()


class CoverageMetricRepository(Repository[CoverageMetric]):
    def __init__(self) -> None:
        super().__init__(CoverageMetric)

    def list_by_snapshot(self, db: Session, snapshot_id: str) -> list[CoverageMetric]:
        statement = select(CoverageMetric).where(CoverageMetric.snapshot_id == snapshot_id)
        return list(db.scalars(statement).all())

    def list_by_type(self, db: Session, snapshot_id: str, metric_type: str) -> list[CoverageMetric]:
        statement = select(CoverageMetric).where(
            CoverageMetric.snapshot_id == snapshot_id,
            CoverageMetric.metric_type == metric_type
        )
        return list(db.scalars(statement).all())
