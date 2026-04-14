from io import StringIO
import csv
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset_revision import AssetRevision
from app.models.audit_log import AuditLog
from app.schemas.asset import AssetRevisionRead
from app.schemas.connector import ConnectorRead
from app.schemas.query import ExportQueryParams, ListQueryParams
from app.schemas.audit import AuditLogRead, AuditOverviewRead
from app.schemas.governance import (
    GovernanceEventDetailRead,
    GovernanceEventKind,
    GovernanceEventRead,
    GovernanceOverviewRead,
    normalize_utc_timestamp,
    parse_utc_timestamp,
    stable_governance_event_id,
)
from app.services.base import BaseService
from app.services.query_filters import (
    apply_case_insensitive_filter,
    apply_contains_filter,
    apply_pagination,
    apply_sort,
)
from app.services.settings_service import SettingsService
from app.core.config import get_settings


class AuditService(BaseService):
    notification_actions = {
        "notification_send",
        "notification_test",
        "notification_skip",
        "notification_fallback",
    }

    @staticmethod
    def _base_logs_statement():
        return select(AuditLog)

    def _apply_log_filters(self, statement, query: ListQueryParams | ExportQueryParams):
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
        statement = apply_sort(
            statement,
            sort=query.sort,
            allowed={
                "id": AuditLog.id,
                "action": AuditLog.action,
                "target_type": AuditLog.target_type,
                "target_id": AuditLog.target_id,
            },
            default="-id",
        )
        return statement

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

    def _to_governance_audit_event(self, log: AuditLog, *, now: datetime | None = None) -> GovernanceEventDetailRead:
        request_json = dict(log.request_json or {})
        response_json = dict(log.response_json or {})
        if log.target_type == "notification" and log.action in self.notification_actions:
            metadata = {}
            if isinstance(request_json.get("metadata"), dict):
                metadata.update(request_json.get("metadata") or {})
            if isinstance(response_json.get("metadata"), dict):
                metadata.update(response_json.get("metadata") or {})
            policy_scope_type = (
                response_json.get("policy_scope_type")
                or metadata.get("notification_policy_scope_type")
            )
            policy_scope_id = (
                response_json.get("policy_scope_id")
                or metadata.get("notification_policy_scope_id")
            )
            event_type = response_json.get("event_type") or request_json.get("event_type")
            channel = response_json.get("channel") or request_json.get("channel")
            provider = response_json.get("provider") or request_json.get("provider")
            status = response_json.get("status")
            target = response_json.get("target") or request_json.get("target")
            environment = response_json.get("environment") or request_json.get("environment")
            project_id = response_json.get("project_id") or request_json.get("project_id")
            fallback_from = response_json.get("fallback_from")
            fallback_reason = response_json.get("fallback_reason")
            severity = "warn" if log.action in {"notification_skip", "notification_fallback"} else "info"
            return GovernanceEventDetailRead(
                id=stable_governance_event_id(log.action, "audit_log", log.id),
                kind=log.action,
                source_type="audit_log",
                source_id=log.id,
                timestamp=normalize_utc_timestamp(now or datetime.now(UTC)),
                severity=severity,
                status=str(status) if status is not None else None,
                target_type=log.target_type,
                target_id=log.target_id,
                project_id=str(project_id) if project_id is not None else None,
                environment=str(environment) if environment is not None else None,
                channel=str(channel) if channel is not None else None,
                provider=str(provider) if provider is not None else None,
                target=str(target) if target is not None else None,
                event_type=str(event_type) if event_type is not None else None,
                policy_scope_type=str(policy_scope_type) if policy_scope_type is not None else None,
                policy_scope_id=str(policy_scope_id) if policy_scope_id is not None else None,
                fallback_from=str(fallback_from) if fallback_from is not None else None,
                fallback_reason=str(fallback_reason) if fallback_reason is not None else None,
                title=f"Notification {log.action}",
                description=f"{channel or provider or 'notification'}:{status or 'unknown'}",
                metadata=metadata,
                raw={
                    "actor_id": log.actor_id,
                    "action": log.action,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "request_json": request_json,
                    "response_json": response_json,
                    "note": log.note,
                },
            )

        source_id = log.id
        payload = {
            "actor_id": log.actor_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "request_json": request_json,
            "response_json": response_json,
            "note": log.note,
        }
        return GovernanceEventDetailRead(
            id=stable_governance_event_id("audit_event", "audit_log", source_id),
            kind="audit_event",
            source_type="audit_log",
            source_id=source_id,
            timestamp=normalize_utc_timestamp(now or datetime.now(UTC)),
            severity="info",
            project_id=str(log.target_id) if log.target_type in {"project", "system"} else None,
            target_type=log.target_type,
            target_id=log.target_id,
            title=f"Audit action: {log.action}",
            description=f"{log.target_type}:{log.target_id}",
            metadata={"actor_id": log.actor_id},
            raw=payload,
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
        statement = self._apply_log_filters(self._base_logs_statement(), query)
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
        statement = self._apply_log_filters(self._base_logs_statement(), query)
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

    def _collect_governance_event_details(self, db: Session, *, now: datetime | None = None) -> list[GovernanceEventDetailRead]:
        from app.services.asset_service import AssetService
        from app.services.connector_service import ConnectorService
        from app.services.gate_service import GateService

        current = (now or datetime.now(UTC)).astimezone(UTC)
        audit_events = [
            self._to_governance_audit_event(log, now=current)
            for log in db.scalars(select(AuditLog).order_by(AuditLog.id.desc())).all()
        ]
        asset_events = AssetService().list_governance_events(db)
        gate_events = GateService().list_governance_events(db, now=current)
        settings_events = SettingsService().list_governance_events()
        connector_events = ConnectorService().list_governance_events(now=current)
        events = [*audit_events, *asset_events, *gate_events, *settings_events, *connector_events]
        events.sort(key=lambda item: parse_utc_timestamp(item.timestamp), reverse=True)
        return events

    def list_governance_events(
        self,
        db: Session,
        *,
        kind: GovernanceEventKind | None = None,
        search: str | None = None,
        project_id: str | None = None,
        environment: str | None = None,
        status: str | None = None,
        channel: str | None = None,
        provider: str | None = None,
        target_type: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        now: datetime | None = None,
        limit: int | None = None,
    ) -> list[GovernanceEventRead]:
        events = self._collect_governance_event_details(db, now=now)
        if kind is not None:
            events = [event for event in events if event.kind == kind]
        if project_id is not None:
            events = [event for event in events if event.project_id == project_id]
        if environment is not None:
            events = [event for event in events if event.environment == environment]
        if status is not None:
            events = [event for event in events if event.status == status]
        if channel is not None:
            events = [event for event in events if event.channel == channel]
        if provider is not None:
            events = [event for event in events if event.provider == provider]
        if target_type is not None:
            events = [event for event in events if event.target_type == target_type]
        if search:
            needle = search.strip().casefold()
            if needle:
                filtered: list[GovernanceEventDetailRead] = []
                for event in events:
                    blob = " ".join(
                        [
                            event.id,
                            event.kind,
                            event.source_type,
                            event.source_id,
                            event.target_type or "",
                            event.target_id or "",
                            event.title,
                            event.description or "",
                            str(event.metadata),
                        ]
                    ).casefold()
                    if needle in blob:
                        filtered.append(event)
                events = filtered
        if page is not None and page_size is not None:
            start = max(page - 1, 0) * page_size
            end = start + page_size
            events = events[start:end]
        if limit is not None:
            events = events[: max(limit, 0)]
        return [GovernanceEventRead.model_validate(event.model_dump()) for event in events]

    def get_governance_event_detail(
        self,
        db: Session,
        event_id: str,
        *,
        now: datetime | None = None,
    ) -> GovernanceEventDetailRead | None:
        events = self._collect_governance_event_details(db, now=now)
        for event in events:
            if event.id == event_id:
                return event
        return None

    def get_governance_overview(self, db: Session, *, now: datetime | None = None) -> GovernanceOverviewRead:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        window_start = current - timedelta(hours=24)
        events = self._collect_governance_event_details(db, now=current)
        recent = [event for event in events if parse_utc_timestamp(event.timestamp) >= window_start]
        connector_errors = [
            event
            for event in recent
            if event.kind == "connector_status" and event.severity in {"error", "blocked"}
        ]
        notification_send_count = sum(
            1
            for event in recent
            if event.kind in self.notification_actions
        )
        notification_test_count = sum(1 for event in recent if event.kind == "notification_test")
        notification_skip_count = sum(1 for event in recent if event.kind == "notification_skip")
        notification_fallback_count = sum(1 for event in recent if event.kind == "notification_fallback")
        ai_fallback_count = sum(
            1
            for event in recent
            if event.kind == "audit_event"
            and event.target_type == "ai_insight"
            and str((event.raw or {}).get("response_json", {}).get("fallback_from") or "").strip() != ""
        )
        settings = get_settings()
        return GovernanceOverviewRead(
            window="last_24h",
            window_start=normalize_utc_timestamp(window_start),
            window_end=normalize_utc_timestamp(current),
            ai_provider=settings.ai_provider,
            ai_model_name=settings.ai_model_name,
            ai_fallback_count=int(ai_fallback_count or 0),
            asset_block_count=sum(1 for event in recent if event.kind == "asset_block"),
            gate_fail_count=sum(1 for event in recent if event.kind == "gate_fail"),
            settings_rollback_count=sum(1 for event in recent if event.kind == "settings_rollback"),
            connector_error_count=len(connector_errors),
            recent_audit_count=sum(1 for event in recent if event.kind == "audit_event"),
            notification_send_count=notification_send_count,
            notification_test_count=notification_test_count,
            notification_skip_count=notification_skip_count,
            notification_fallback_count=notification_fallback_count,
            recent_events=[
                GovernanceEventRead.model_validate(event.model_dump())
                for event in recent[:10]
            ],
        )
