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

    def list_logs(
        self,
        db: Session,
        *,
        search: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[AuditLogRead]:
        logs = list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc())).all())
        if search:
            lowered = search.lower()
            logs = [
                log
                for log in logs
                if lowered in log.id.lower()
                or lowered in (log.action or "").lower()
                or lowered in (log.target_type or "").lower()
                or lowered in (log.target_id or "").lower()
            ]
        if action:
            logs = [log for log in logs if log.action == action]
        if target_type:
            logs = [log for log in logs if log.target_type == target_type]
        start = max(page - 1, 0) * page_size
        end = start + page_size
        logs = logs[start:end]
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

    def export_logs_csv(
        self,
        db: Session,
        *,
        search: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
    ) -> str:
        logs = self.list_logs(db, search=search, action=action, target_type=target_type, page=1, page_size=1000)
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "actor_id", "action", "target_type", "target_id"])
        for log in logs:
            writer.writerow([log.id, log.actor_id or "", log.action, log.target_type, log.target_id])
        return buffer.getvalue()
from io import StringIO
import csv
