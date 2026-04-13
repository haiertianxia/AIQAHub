from __future__ import annotations

from typing import Any

from app.core.exceptions import ValidationError
from app.notifications.dingtalk import DingTalkNotifier
from app.notifications.email import EmailNotifier
from app.notifications.wecom import WeComNotifier
from app.schemas.settings import SettingsRead


class Notifier:
    def __init__(self, settings: SettingsRead) -> None:
        self.settings = settings

    def _build_provider(self, channel: str | None = None):
        resolved = (channel or self.settings.notification_default_channel or "dingtalk").strip().lower()
        if resolved == "email":
            if not self.settings.notification_email_enabled:
                raise ValidationError("email notifications are disabled")
            return EmailNotifier(
                smtp_host=self.settings.notification_email_smtp_host,
                smtp_port=self.settings.notification_email_smtp_port,
                sender=self.settings.notification_email_from,
                recipients=self.settings.notification_email_to,
            )
        if resolved == "dingtalk":
            if not self.settings.notification_dingtalk_enabled:
                raise ValidationError("dingtalk notifications are disabled")
            return DingTalkNotifier(webhook_url=self.settings.notification_dingtalk_webhook_url)
        if resolved == "wecom":
            if not self.settings.notification_wecom_enabled:
                raise ValidationError("wecom notifications are disabled")
            return WeComNotifier(webhook_url=self.settings.notification_wecom_webhook_url)
        raise ValidationError(f"Unsupported notification channel: {resolved}")

    def notify(
        self,
        *,
        message: str,
        subject: str | None = None,
        channel: str | None = None,
        target: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        provider = self._build_provider(channel)
        return provider.send(message=message, subject=subject, target=target, metadata=metadata)
