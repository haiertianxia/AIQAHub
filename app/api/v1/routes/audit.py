from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService

router = APIRouter()
service = AuditService()


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    action: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> list[AuditLogRead]:
    return service.list_logs(
        db,
        search=search,
        action=action,
        target_type=target_type,
        page=page,
        page_size=page_size,
    )
