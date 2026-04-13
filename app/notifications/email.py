from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from app.core.exceptions import ValidationError
from app.notifications.base import NotificationProvider


class EmailNotifier(NotificationProvider):
    channel = "email"

    def __init__(
        self,
        *,
        smtp_host: str,
        smtp_port: int,
        sender: str,
        recipients: str,
        username: str = "",
        password: str = "",
        timeout_seconds: int = 10,
    ) -> None:
        self.smtp_host = smtp_host.strip()
        self.smtp_port = int(smtp_port)
        self.sender = sender.strip()
        self.recipients = recipients.strip()
        self.username = username.strip()
        self.password = password
        self.timeout_seconds = int(timeout_seconds)

    @staticmethod
    def _split_recipients(recipients: str) -> list[str]:
        return [item.strip() for item in recipients.split(",") if item.strip()]

    def send(
        self,
        *,
        message: str,
        subject: str | None = None,
        target: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        recipients = self._split_recipients(target or self.recipients)
        if not self.smtp_host or not self.sender or not recipients:
            raise ValidationError("email notification is not configured")

        email = EmailMessage()
        email["From"] = self.sender
        email["To"] = ", ".join(recipients)
        email["Subject"] = subject or "AIQAHub notification"
        body = message
        if metadata:
            body = f"{body}\n\nmetadata={metadata}"
        email.set_content(body)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout_seconds) as client:
                client.send_message(email)
        except (OSError, smtplib.SMTPException) as exc:
            raise ValidationError(f"email notification failed: {exc}") from exc

        return {
            "channel": self.channel,
            "provider": self.channel,
            "status": "success",
            "message": message,
            "target": ",".join(recipients),
            "details": {
                "smtp_host": self.smtp_host,
                "smtp_port": self.smtp_port,
                "sender": self.sender,
            },
        }
