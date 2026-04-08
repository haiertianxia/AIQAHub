from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import ReportIndexItem, ReportSummary
from app.services.report_service import ReportService

router = APIRouter()
service = ReportService()


@router.get("", response_model=list[ReportIndexItem])
def list_reports(db: Session = Depends(get_db)) -> list[ReportIndexItem]:
    return service.list_reports(db)


@router.get("/{execution_id}", response_model=ReportSummary)
def get_report(execution_id: str, db: Session = Depends(get_db)) -> ReportSummary:
    return service.get_report(db, execution_id)
