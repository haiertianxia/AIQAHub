from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.schemas.notification import NotificationPolicyRead, NotificationSendRequest
from app.services.base import BaseService
from app.services.settings_service import SettingsService


@dataclass(slots=True)
class ResolvedNotificationPolicy:
    policy: NotificationPolicyRead | None
    channel: str
    target: str | None
    subject: str | None = None


class _SafeFormatDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:  # pragma: no cover - defensive
        return ""


class NotificationPolicyService(BaseService):
    def __init__(self) -> None:
        self.settings_service = SettingsService()

    @staticmethod
    def _as_list(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, Iterable):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @staticmethod
    def _event_type(payload: NotificationSendRequest) -> str:
        return (payload.event_type or "notification_test").strip().lower()

    @staticmethod
    def _scope_rank(policy: NotificationPolicyRead, project_id: str | None) -> int:
        if policy.scope_type == "project" and project_id and policy.scope_id == project_id:
            return 0
        if policy.scope_type == "global":
            return 1
        return 2

    def _matches_filters(
        self,
        policy: NotificationPolicyRead,
        *,
        project_id: str | None,
        environment: str | None,
        severity: str | None,
    ) -> bool:
        filters = policy.filters or {}
        for key, actual in {
            "project_id": project_id,
            "env_type": environment,
            "severity": severity,
        }.items():
            allowed = self._as_list(filters.get(key))
            if allowed and (actual is None or actual not in allowed):
                return False
        return True

    def _candidate_policies(
        self,
        *,
        payload: NotificationSendRequest,
        environment: str | None,
    ) -> list[NotificationPolicyRead]:
        settings = self.settings_service.get_settings(environment)
        event_type = self._event_type(payload)
        project_id = payload.project_id
        severity = payload.metadata.get("severity") if isinstance(payload.metadata, dict) else None
        candidates: list[tuple[int, NotificationPolicyRead]] = []
        for policy in settings.notification_policies:
            if policy.event_type.strip().lower() != event_type:
                continue
            if not policy.enabled:
                continue
            if not self._matches_filters(policy, project_id=project_id, environment=environment, severity=severity):
                continue
            candidates.append((self._scope_rank(policy, project_id), policy))
        candidates.sort(key=lambda item: (item[0], item[1].scope_type, item[1].scope_id))
        return [policy for _, policy in candidates]

    def resolve(self, payload: NotificationSendRequest, *, environment: str | None = None) -> ResolvedNotificationPolicy:
        candidates = self._candidate_policies(payload=payload, environment=environment)
        if not candidates:
            settings = self.settings_service.get_settings(environment)
            channel = (payload.channel or settings.notification_default_channel or "dingtalk").strip().lower()
            return ResolvedNotificationPolicy(policy=None, channel=channel, target=payload.target, subject=payload.subject)

        policy = candidates[0]
        channel = policy.channels[0] if policy.channels else (payload.channel or self.settings_service.get_settings(environment).notification_default_channel)
        subject = payload.subject
        if policy.subject_template:
            subject = policy.subject_template.format_map(
                _SafeFormatDict(
                    {
                        "event_type": self._event_type(payload),
                        "project_id": payload.project_id or "",
                        "environment": environment or "",
                        "channel": channel,
                        "target": policy.target or payload.target or "",
                        "message": payload.message,
                    }
                )
            )
        return ResolvedNotificationPolicy(policy=policy, channel=channel, target=policy.target or payload.target, subject=subject)

    def route(self, payload: NotificationSendRequest, *, environment: str | None = None) -> NotificationSendRequest:
        resolved = self.resolve(payload, environment=environment)
        metadata = dict(payload.metadata)
        if resolved.policy is not None:
            metadata.update(
                {
                    "notification_policy_scope_type": resolved.policy.scope_type,
                    "notification_policy_scope_id": resolved.policy.scope_id,
                    "notification_policy_event_type": resolved.policy.event_type,
                }
            )
        return NotificationSendRequest(
            channel=resolved.channel,
            subject=resolved.subject or payload.subject,
            message=payload.message,
            target=resolved.target,
            metadata=metadata,
            event_type=payload.event_type,
            project_id=payload.project_id,
        )
