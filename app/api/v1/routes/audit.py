from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.query import ExportQueryParams, ListQueryParams
from app.schemas.audit import AuditLogRead, AuditOverviewRead
from app.services.audit_service import AuditService

router = APIRouter()
service = AuditService()


@router.get("/overview", response_model=AuditOverviewRead)
def get_audit_overview(db: Session = Depends(get_db)) -> AuditOverviewRead:
    return service.get_overview(db)


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    action: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> list[AuditLogRead]:
    query = ListQueryParams(
        search=search,
        action=action,
        target_type=target_type,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return service.list_logs(db, query=query)


@router.get("/export")
def export_audit_logs(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    action: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    sort: str | None = Query(default=None),
) -> Response:
    query = ExportQueryParams(search=search, action=action, target_type=target_type, sort=sort)
    csv_text = service.export_logs_csv(db, query=query)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="audit-logs.csv"'},
    )
