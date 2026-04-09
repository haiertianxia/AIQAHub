from __future__ import annotations

import hashlib
import hmac
import threading
import time
from collections.abc import Mapping

from app.core.exceptions import ValidationError

WEBHOOK_SIGNATURE_HEADER = "x-aiqa-signature"
WEBHOOK_TIMESTAMP_HEADER = "x-aiqa-timestamp"
WEBHOOK_NONCE_HEADER = "x-aiqa-nonce"
WEBHOOK_EXECUTION_ID_HEADER = "x-aiqa-execution-id"


class WebhookReplayCache:
    def __init__(self) -> None:
        self._nonces: dict[str, float] = {}
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._nonces.clear()

    def remember(self, nonce: str, ttl_seconds: int) -> None:
        now = time.time()
        expires_at = now + ttl_seconds
        with self._lock:
            self._purge_expired_locked(now)
            previous_expiry = self._nonces.get(nonce)
            if previous_expiry is not None and previous_expiry > now:
                raise ValidationError("duplicate Jenkins webhook nonce")
            self._nonces[nonce] = expires_at

    def _purge_expired_locked(self, now: float) -> None:
        expired = [nonce for nonce, expiry in self._nonces.items() if expiry <= now]
        for nonce in expired:
            self._nonces.pop(nonce, None)


replay_cache = WebhookReplayCache()


def _normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}


def _signature_message(timestamp: str, nonce: str, execution_id: str, body: bytes) -> bytes:
    return b"\n".join(
        [
            timestamp.encode("utf-8"),
            nonce.encode("utf-8"),
            execution_id.encode("utf-8"),
            body,
        ]
    )


def compute_jenkins_webhook_signature(
    *,
    secret: str,
    timestamp: str,
    nonce: str,
    execution_id: str,
    body: bytes,
) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        _signature_message(timestamp, nonce, execution_id, body),
        hashlib.sha256,
    ).hexdigest()


def verify_jenkins_webhook(
    *,
    secret: str,
    headers: Mapping[str, str],
    body: bytes,
    max_skew_seconds: int,
) -> None:
    normalized = _normalize_headers(headers)
    timestamp = normalized.get(WEBHOOK_TIMESTAMP_HEADER)
    nonce = normalized.get(WEBHOOK_NONCE_HEADER)
    signature = normalized.get(WEBHOOK_SIGNATURE_HEADER)
    execution_id = normalized.get(WEBHOOK_EXECUTION_ID_HEADER)

    if not secret:
        raise ValidationError("jenkins webhook secret is not configured")
    if not timestamp or not nonce or not signature or not execution_id:
        raise ValidationError("missing Jenkins webhook verification headers")

    try:
        timestamp_value = int(timestamp)
    except ValueError as exc:
        raise ValidationError("invalid Jenkins webhook timestamp") from exc

    now = int(time.time())
    if abs(now - timestamp_value) > max_skew_seconds:
        raise ValidationError("Jenkins webhook timestamp outside allowed window")

    expected_signature = compute_jenkins_webhook_signature(
        secret=secret,
        timestamp=timestamp,
        nonce=nonce,
        execution_id=execution_id,
        body=body,
    )
    signature_value = signature.removeprefix("sha256=").lower()
    if not hmac.compare_digest(expected_signature, signature_value):
        raise ValidationError("invalid Jenkins webhook signature")

    replay_cache.remember(nonce, max_skew_seconds)

