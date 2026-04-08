from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService

router = APIRouter()
service = AuditService()


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(db: Session = Depends(get_db)) -> list[AuditLogRead]:
    return service.list_logs(db)
