from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogRead
from app.services.base import BaseService


class AuditService(BaseService):
    def record(
        self,
        db: Session,
        *,
        actor_id: str | None,
        action: str,
        target_type: str,
        target_id: str,
        request_json: dict | None = None,
        response_json: dict | None = None,
        note: str | None = None,
    ) -> None:
        log = AuditLog(
            id=f"audit_{uuid4().hex[:12]}",
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            request_json=request_json,
            response_json=response_json,
            note=note,
        )
        db.add(log)
        db.commit()

    def list_logs(self, db: Session) -> list[AuditLogRead]:
        logs = list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc())).all())
        return [
            AuditLogRead(
                id=log.id,
                actor_id=log.actor_id,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                request_json=log.request_json or {},
                response_json=log.response_json or {},
            )
            for log in logs
        ]
