from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from app.core.exceptions import ValidationError
from app.notifications.base import NotificationProvider


class DingTalkNotifier(NotificationProvider):
    channel = "dingtalk"

    def __init__(self, *, webhook_url: str, timeout_seconds: int = 10) -> None:
        self.webhook_url = webhook_url.strip()
        self.timeout_seconds = int(timeout_seconds)

    @staticmethod
    def _render_content(message: str, subject: str | None = None, metadata: dict[str, Any] | None = None) -> str:
        parts = [part for part in [subject, message] if part]
        content = "\n".join(parts)
        if metadata:
            content = f"{content}\n\nmetadata={json.dumps(metadata, ensure_ascii=False, sort_keys=True)}"
        return content

    def send(
        self,
        *,
        message: str,
        subject: str | None = None,
        target: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = (target or self.webhook_url).strip()
        if not url:
            raise ValidationError("dingtalk notification is not configured")

        content = self._render_content(message, subject, metadata)
        payload = {"msgtype": "text", "text": {"content": content}}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                response.read()
        except error.URLError as exc:
            raise ValidationError(f"dingtalk notification failed: {exc}") from exc

        return {
            "channel": self.channel,
            "provider": self.channel,
            "status": "success",
            "message": content,
            "target": url,
            "details": {"webhook_url": url},
        }
