from io import StringIO
import csv
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.query import ExportQueryParams, ListQueryParams
from app.schemas.audit import AuditLogRead
from app.services.base import BaseService
from app.services.query_filters import (
    apply_case_insensitive_filter,
    apply_contains_filter,
    apply_pagination,
)


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

    def list_logs(self, db: Session, *, query: ListQueryParams) -> list[AuditLogRead]:
        statement = select(AuditLog).order_by(AuditLog.id.desc())
        statement = apply_case_insensitive_filter(statement, AuditLog.action, query.action)
        statement = apply_case_insensitive_filter(statement, AuditLog.target_type, query.target_type)
        statement = apply_contains_filter(
            statement,
            [
                AuditLog.id,
                AuditLog.actor_id,
                AuditLog.action,
                AuditLog.target_type,
                AuditLog.target_id,
                AuditLog.request_json,
                AuditLog.response_json,
                AuditLog.note,
            ],
            query.search,
        )
        statement = apply_pagination(statement, page=query.page, page_size=query.page_size)
        logs = list(db.scalars(statement).all())
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

    def export_logs_csv(self, db: Session, *, query: ExportQueryParams) -> str:
        statement = select(AuditLog).order_by(AuditLog.id.desc())
        statement = apply_case_insensitive_filter(statement, AuditLog.action, query.action)
        statement = apply_case_insensitive_filter(statement, AuditLog.target_type, query.target_type)
        statement = apply_contains_filter(
            statement,
            [
                AuditLog.id,
                AuditLog.actor_id,
                AuditLog.action,
                AuditLog.target_type,
                AuditLog.target_id,
                AuditLog.request_json,
                AuditLog.response_json,
                AuditLog.note,
            ],
            query.search,
        )
        logs = [
            AuditLogRead(
                id=log.id,
                actor_id=log.actor_id,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                request_json=log.request_json or {},
                response_json=log.response_json or {},
            )
            for log in db.scalars(statement).all()
        ]
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "actor_id", "action", "target_type", "target_id"])
        for log in logs:
            writer.writerow([log.id, log.actor_id or "", log.action, log.target_type, log.target_id])
        return buffer.getvalue()
