from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import (
    CoverageSnapshotCreate,
    CoverageSnapshotRead,
    CoverageMetricCreate,
    CoverageMetricRead,
)
from app.services.document_service import CoverageService

router = APIRouter(prefix="/coverage", tags=["coverage"])
coverage_service = CoverageService()


# Coverage Snapshot endpoints
@router.get("/snapshots", response_model=list[CoverageSnapshotRead])
def list_coverage_snapshots(
    project_id: str = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
) -> list[CoverageSnapshotRead]:
    return coverage_service.list_snapshots(db, project_id)


@router.get("/snapshots/{snapshot_id}", response_model=CoverageSnapshotRead)
def get_coverage_snapshot(snapshot_id: str, db: Session = Depends(get_db)) -> CoverageSnapshotRead:
    return coverage_service.get_snapshot(db, snapshot_id)


@router.post("/snapshots", response_model=CoverageSnapshotRead)
def create_coverage_snapshot(
    payload: CoverageSnapshotCreate,
    db: Session = Depends(get_db),
) -> CoverageSnapshotRead:
    return coverage_service.create_snapshot(db, payload)


# Coverage Metric endpoints
@router.get("/snapshots/{snapshot_id}/metrics", response_model=list[CoverageMetricRead])
def list_coverage_metrics(
    snapshot_id: str,
    db: Session = Depends(get_db),
) -> list[CoverageMetricRead]:
    return coverage_service.list_metrics(db, snapshot_id)


@router.post("/snapshots/{snapshot_id}/metrics", response_model=CoverageMetricRead)
def create_coverage_metric(
    snapshot_id: str,
    payload: CoverageMetricCreate,
    db: Session = Depends(get_db),
) -> CoverageMetricRead:
    return coverage_service.create_metric(db, payload)
