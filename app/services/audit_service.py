from io import StringIO
import csv
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset_revision import AssetRevision
from app.models.audit_log import AuditLog
from app.schemas.asset import AssetRevisionRead
from app.schemas.connector import ConnectorRead
from app.schemas.query import ExportQueryParams, ListQueryParams
from app.schemas.audit import AuditLogRead, AuditOverviewRead
from app.services.base import BaseService
from app.services.query_filters import (
    apply_case_insensitive_filter,
    apply_contains_filter,
    apply_pagination,
)
from app.services.settings_service import SettingsService


class AuditService(BaseService):
    @staticmethod
    def _to_asset_revision_read(revision: AssetRevision) -> AssetRevisionRead:
        return AssetRevisionRead(
            id=revision.id,
            asset_id=revision.asset_id,
            revision_number=revision.revision_number,
            version=revision.version,
            snapshot=revision.snapshot_json,
            change_summary=revision.change_summary,
            created_by=revision.created_by,
            created_at=revision.created_at,
        )

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

    def get_overview(self, db: Session) -> AuditOverviewRead:
        audit_log_count = int(db.scalar(select(func.count()).select_from(AuditLog)) or 0)
        gate_change_count = int(
            db.scalar(
                select(func.count()).select_from(AuditLog).where(AuditLog.target_type == "quality_rule")
            )
            or 0
        )
        asset_revision_count = int(db.scalar(select(func.count()).select_from(AssetRevision)) or 0)

        recent_audit_logs = [
            AuditLogRead(
                id=log.id,
                actor_id=log.actor_id,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                request_json=log.request_json or {},
                response_json=log.response_json or {},
            )
            for log in db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(5)).all()
        ]
        recent_gate_changes = [
            AuditLogRead(
                id=log.id,
                actor_id=log.actor_id,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                request_json=log.request_json or {},
                response_json=log.response_json or {},
            )
            for log in db.scalars(
                select(AuditLog).where(AuditLog.target_type == "quality_rule").order_by(AuditLog.id.desc()).limit(5)
            ).all()
        ]
        recent_asset_revisions = list(
            db.scalars(select(AssetRevision).order_by(AssetRevision.created_at.desc()).limit(5)).all()
        )
        settings_service = SettingsService()
        all_settings_history = settings_service.list_all_history()
        recent_settings_history = all_settings_history[:5]
        connector_reads = [
            ConnectorRead(connector_type="jenkins", ok=True, status="created", message="Jenkins connector available"),
            ConnectorRead(connector_type="llm", ok=True, status="created", message="LLM connector available"),
            ConnectorRead(connector_type="playwright", ok=True, status="created", message="Playwright connector available"),
        ]
        return AuditOverviewRead(
            audit_log_count=audit_log_count,
            gate_change_count=gate_change_count,
            settings_revision_count=len(all_settings_history),
            asset_revision_count=asset_revision_count,
            connector_count=len(connector_reads),
            connectors=connector_reads,
            recent_audit_logs=recent_audit_logs,
            recent_gate_changes=recent_gate_changes,
            recent_settings_history=recent_settings_history,
            recent_asset_revisions=[self._to_asset_revision_read(revision) for revision in recent_asset_revisions],
        )
