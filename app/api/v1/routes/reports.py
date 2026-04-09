from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import ReportIndexItem, ReportSummary
from app.services.report_service import ReportService

router = APIRouter()
service = ReportService()


@router.get("", response_model=list[ReportIndexItem])
def list_reports(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    completion_source: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> list[ReportIndexItem]:
    return service.list_reports(
        db,
        search=search,
        status=status,
        completion_source=completion_source,
        page=page,
        page_size=page_size,
    )


@router.get("/{execution_id}", response_model=ReportSummary)
def get_report(execution_id: str, db: Session = Depends(get_db)) -> ReportSummary:
    return service.get_report(db, execution_id)
