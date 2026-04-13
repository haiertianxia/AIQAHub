from __future__ import annotations

from typing import Any

from app.core.exceptions import ValidationError
from app.notifications.notifier import Notifier
from app.schemas.notification import NotificationSendRead, NotificationSendRequest
from app.schemas.execution import ExecutionRead
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

    def send(
        self,
        payload: NotificationSendRequest,
        *,
        environment: str | None = None,
    ) -> NotificationSendRead:
        routed_payload = self.policy_service.route(payload, environment=environment)
        try:
            notifier = self._notifier(environment)
            result = notifier.notify(
                message=routed_payload.message,
                subject=routed_payload.subject,
                channel=routed_payload.channel,
                target=routed_payload.target,
                metadata=routed_payload.metadata,
            )
            return NotificationSendRead.model_validate(result)
        except ValidationError as exc:
            resolved_channel = routed_payload.channel.strip().lower()
            status = "skipped" if "disabled" in str(exc).lower() or "not configured" in str(exc).lower() else "failed"
            return NotificationSendRead(
                channel=resolved_channel,
                provider=resolved_channel,
                status=status,
                message=payload.message,
                target=routed_payload.target or payload.target,
                details={"reason": str(exc)},
            )

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
