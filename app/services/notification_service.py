from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.core.exceptions import ValidationError
from app.db.session import SessionLocal
from app.notifications.notifier import Notifier
from app.schemas.notification import NotificationSendRead, NotificationSendRequest
from app.schemas.execution import ExecutionRead
from app.services.audit_service import AuditService
from app.services.base import BaseService
from app.services.notification_policy_service import NotificationPolicyService
from app.services.settings_service import SettingsService


class NotificationService(BaseService):
    def __init__(self) -> None:
        self.settings_service = SettingsService()
        self.policy_service = NotificationPolicyService()

    def _notifier(self, environment: str | None = None) -> Notifier:
        settings = self.settings_service.get_settings(environment)
        return Notifier(settings)

    @staticmethod
    def _normalize_event_type(payload: NotificationSendRequest) -> str:
        return (payload.event_type or "notification_test").strip().lower()

    @staticmethod
    def _normalize_channel(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    @staticmethod
    def _derive_target_id(payload: NotificationSendRequest) -> str:
        metadata = payload.metadata if isinstance(payload.metadata, dict) else {}
        for key in ("execution_id", "gate_id", "settings_id", "test_token"):
            value = metadata.get(key)
            if value is not None:
                text = str(value).strip()
                if text:
                    return text[:64]
        if payload.project_id:
            return str(payload.project_id)[:64]
        return f"notif_{uuid4().hex[:12]}"

    def _audit_action(
        self,
        *,
        payload: NotificationSendRequest,
        result: NotificationSendRead,
    ) -> str:
        event_type = self._normalize_event_type(payload)
        fallback_from = result.details.get("fallback_from") if isinstance(result.details, dict) else None
        if event_type in {"notification_send", "notification_test", "notification_skip", "notification_fallback"}:
            return event_type
        if fallback_from:
            return "notification_fallback"
        if result.status == "skipped":
            return "notification_skip"
        return "notification_send"

    def _audit_notification(
        self,
        *,
        payload: NotificationSendRequest,
        routed_payload: NotificationSendRequest,
        result: NotificationSendRead,
        environment: str | None,
    ) -> None:
        event_type = self._normalize_event_type(payload)
        request_json = {
            "event_type": event_type,
            "project_id": payload.project_id,
            "channel": self._normalize_channel(payload.channel),
            "provider": self._normalize_channel(payload.channel),
            "status": "requested",
            "target": payload.target,
            "environment": environment,
            "metadata": dict(payload.metadata),
        }
        response_json = {
            "event_type": event_type,
            "project_id": payload.project_id,
            "channel": result.channel,
            "provider": result.provider,
            "status": result.status,
            "target": result.target,
            "environment": environment,
            "metadata": dict(routed_payload.metadata),
            "policy_scope_type": routed_payload.metadata.get("notification_policy_scope_type"),
            "policy_scope_id": routed_payload.metadata.get("notification_policy_scope_id"),
            "fallback_from": result.details.get("fallback_from") if isinstance(result.details, dict) else None,
            "fallback_reason": result.details.get("fallback_reason") if isinstance(result.details, dict) else None,
        }
        action = self._audit_action(payload=payload, result=result)
        target_id = self._derive_target_id(payload)

        with SessionLocal() as db:
            AuditService().record(
                db,
                actor_id="system",
                action=action,
                target_type="notification",
                target_id=target_id,
                request_json=request_json,
                response_json=response_json,
                note=f"notification event_type={event_type}",
            )

    def send(
        self,
        payload: NotificationSendRequest,
        *,
        environment: str | None = None,
    ) -> NotificationSendRead:
        routed_payload = self.policy_service.route(payload, environment=environment)
        fallback_from: str | None = None
        fallback_reason: str | None = None
        original_channel = self._normalize_channel(payload.channel)
        routed_channel = self._normalize_channel(routed_payload.channel)
        if original_channel and routed_channel and original_channel != routed_channel:
            fallback_from = original_channel
            fallback_reason = "policy_reroute"
        try:
            notifier = self._notifier(environment)
            result = notifier.notify(
                message=routed_payload.message,
                subject=routed_payload.subject,
                channel=routed_payload.channel,
                target=routed_payload.target,
                metadata=routed_payload.metadata,
            )
            notification = NotificationSendRead.model_validate(result)
            if fallback_from:
                notification.details["fallback_from"] = fallback_from
                notification.details["fallback_reason"] = fallback_reason
        except ValidationError as exc:
            resolved_channel = routed_payload.channel.strip().lower()
            status = "skipped" if "disabled" in str(exc).lower() or "not configured" in str(exc).lower() else "failed"
            notification = NotificationSendRead(
                channel=resolved_channel,
                provider=resolved_channel,
                status=status,
                message=payload.message,
                target=routed_payload.target or payload.target,
                details={
                    "reason": str(exc),
                    "fallback_from": fallback_from,
                    "fallback_reason": fallback_reason or str(exc),
                },
            )
        try:
            self._audit_notification(
                payload=payload,
                routed_payload=routed_payload,
                result=notification,
                environment=environment,
            )
        except Exception:
            # Notification delivery should remain non-blocking even if governance audit projection fails.
            pass
        return notification

    def notify_execution_failure(self, execution: ExecutionRead | dict[str, Any], *, environment: str | None = None) -> NotificationSendRead:
        if isinstance(execution, ExecutionRead):
            execution_data = execution.model_dump()
        else:
            execution_data = dict(execution)
        settings = self.settings_service.get_settings(environment)
        subject = f"Execution failed: {execution_data.get('id', 'unknown')}"
        message = (
            f"execution={execution_data.get('id', 'unknown')} "
            f"status={execution_data.get('status', 'unknown')} "
            f"completion_source={execution_data.get('completion_source', 'unknown')} "
            f"project={execution_data.get('project_id', 'unknown')} "
            f"suite={execution_data.get('suite_id', 'unknown')}"
        )
        payload = NotificationSendRequest(
            channel=settings.notification_default_channel,
            subject=subject,
            message=message,
            metadata={"kind": "execution_failure", "execution_id": execution_data.get("id", "unknown")},
            event_type="execution_failed",
            project_id=execution_data.get("project_id", "unknown"),
        )
        return self.send(payload, environment=environment)

    def notify_gate_failure(self, gate_result: dict[str, Any], *, environment: str | None = None) -> NotificationSendRead:
        settings = self.settings_service.get_settings(environment)
        subject = f"Gate failed: {gate_result.get('execution_id', 'unknown')}"
        message = (
            f"execution={gate_result.get('execution_id', 'unknown')} "
            f"result={gate_result.get('result', 'unknown')} "
            f"score={gate_result.get('score', 0)} "
            f"reason={gate_result.get('reason', 'unknown')}"
        )
        payload = NotificationSendRequest(
            channel=settings.notification_default_channel,
            subject=subject,
            message=message,
            metadata={"kind": "gate_failure", "execution_id": gate_result.get("execution_id", "unknown")},
            event_type="gate_failed",
            project_id=gate_result.get("project_id", "unknown"),
        )
        return self.send(payload, environment=environment)
