import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.settings_service import SettingsService


@pytest.fixture(autouse=True)
def isolated_settings_store(monkeypatch, tmp_path):
    # Keep notification/governance tests hermetic: settings overrides/history should not leak
    # across test modules or runs.
    monkeypatch.setattr(SettingsService, "overrides_path", tmp_path / "settings_overrides.json")
    monkeypatch.setattr(SettingsService, "history_path", tmp_path / "settings_history.json")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _client() -> TestClient:
    return TestClient(app)


def _start_webhook_server(*, status_code: int = 200) -> tuple[HTTPServer, threading.Thread, dict[str, object]]:
    received: dict[str, object] = {"count": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            received["count"] = int(received["count"]) + 1
            received["path"] = self.path
            received["payload"] = json.loads(body)
            encoded = json.dumps({"ok": status_code == 200}).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, received


def _webhook_url(server: HTTPServer, path: str) -> str:
    return f"http://127.0.0.1:{server.server_port}{path}"


def _configure_notification_settings(
    client: TestClient,
    *,
    environment: str,
    default_channel: str,
    dingtalk_url: str,
    wecom_url: str,
    policies: list[dict[str, object]] | None = None,
) -> None:
    payload: dict[str, object] = {
        "notification_default_channel": default_channel,
        "notification_dingtalk_enabled": True,
        "notification_dingtalk_webhook_url": dingtalk_url,
        "notification_wecom_enabled": True,
        "notification_wecom_webhook_url": wecom_url,
    }
    if policies is not None:
        payload["notification_policies"] = policies

    response = client.put(f"/api/v1/settings?environment={environment}", json=payload)
    assert response.status_code == 200


def test_notification_sends_are_projected_into_governance_event_stream(monkeypatch):
    """
    Required behavior:
    1. Notification sends appear in governance overview or event stream.

    This test asserts projection into the governance event stream. It should fail until
    Task 2 implements notification governance history projection.
    """

    environment = f"qa_gov_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    server, thread, received = _start_webhook_server()
    token = f"gov_notify_token_{uuid4().hex}"
    try:
        client = _client()
        _configure_notification_settings(
            client,
            environment=environment,
            default_channel="dingtalk",
            dingtalk_url=_webhook_url(server, "/dingtalk"),
            wecom_url=_webhook_url(server, "/wecom"),
        )

        send_response = client.post(
            f"/api/v1/notifications/test?environment={environment}",
            json={
                "channel": "dingtalk",
                "subject": "Governance notification projection test",
                "message": f"notification send token={token}",
                "metadata": {"test_token": token},
                "event_type": "notification_test",
                "project_id": "proj_demo",
            },
        )
        assert send_response.status_code == 200
        assert send_response.json()["status"] == "success"
        assert received["count"] == 1

        events_response = client.get(f"/api/v1/governance/events?search={token}&limit=50")
        assert events_response.status_code == 200
        events = events_response.json()

        notification_events = [event for event in events if event.get("kind") == "notification_send"]
        assert notification_events, "expected governance events to include notification_send items"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        get_settings.cache_clear()


def test_notification_governance_events_can_be_filtered_by_kind_channel_and_provider(monkeypatch):
    """
    Required behavior:
    2. Notification events can be filtered by kind and channel/provider.

    This test intentionally fails until Task 2 extends the governance event kinds and filtering.
    """

    environment = f"qa_gov_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    dingtalk_server, dingtalk_thread, _ = _start_webhook_server()
    wecom_server, wecom_thread, _ = _start_webhook_server()
    token_a = f"gov_notify_token_{uuid4().hex}"
    token_b = f"gov_notify_token_{uuid4().hex}"
    try:
        client = _client()
        _configure_notification_settings(
            client,
            environment=environment,
            default_channel="dingtalk",
            dingtalk_url=_webhook_url(dingtalk_server, "/dingtalk"),
            wecom_url=_webhook_url(wecom_server, "/wecom"),
        )

        for channel, token in [("dingtalk", token_a), ("wecom", token_b)]:
            send_response = client.post(
                f"/api/v1/notifications/test?environment={environment}",
                json={
                    "channel": channel,
                    "subject": f"Governance filter test {channel}",
                    "message": f"notification send token={token}",
                    "metadata": {"test_token": token},
                    "event_type": "notification_test",
                    "project_id": "proj_demo",
                },
            )
            assert send_response.status_code == 200
            assert send_response.json()["status"] == "success"

        # Filter by kind AND channel.
        channel_response = client.get("/api/v1/governance/events?kind=notification_send&channel=dingtalk&limit=50")
        assert channel_response.status_code == 200
        channel_events = channel_response.json()
        assert channel_events
        assert {event.get("metadata", {}).get("channel") for event in channel_events} == {"dingtalk"}

        # Filter by kind AND provider.
        provider_response = client.get("/api/v1/governance/events?kind=notification_send&provider=wecom&limit=50")
        assert provider_response.status_code == 200
        provider_events = provider_response.json()
        assert provider_events
        assert {event.get("metadata", {}).get("provider") for event in provider_events} == {"wecom"}
    finally:
        dingtalk_server.shutdown()
        dingtalk_thread.join(timeout=2)
        wecom_server.shutdown()
        wecom_thread.join(timeout=2)
        get_settings.cache_clear()


def test_notification_governance_event_detail_includes_policy_and_fallback_metadata(monkeypatch):
    """
    Required behavior:
    3. Notification event detail includes policy and fallback metadata.

    The "policy" metadata is expected to align with NotificationPolicyService routing keys.
    The "fallback" metadata is required even when no fallback is used.
    """

    environment = f"qa_gov_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    server, thread, _ = _start_webhook_server()
    token = f"gov_notify_token_{uuid4().hex}"
    try:
        client = _client()
        _configure_notification_settings(
            client,
            environment=environment,
            default_channel="wecom",
            dingtalk_url=_webhook_url(server, "/dingtalk"),
            wecom_url=_webhook_url(server, "/wecom"),
            policies=[
                {
                    "scope_type": "project",
                    "scope_id": "proj_demo",
                    "event_type": "notification_test",
                    "enabled": True,
                    "channels": ["dingtalk"],
                    "subject_template": "Policy routed {event_type} ({project_id})",
                    "target": _webhook_url(server, "/dingtalk"),
                    "filters": {"project_id": ["proj_demo"]},
                }
            ],
        )

        send_response = client.post(
            f"/api/v1/notifications/test?environment={environment}",
            json={
                "channel": "wecom",
                "subject": "Governance notification detail test",
                "message": f"notification send token={token}",
                "metadata": {"test_token": token},
                "event_type": "notification_test",
                "project_id": "proj_demo",
            },
        )
        assert send_response.status_code == 200

        events_response = client.get(f"/api/v1/governance/events?kind=notification_send&search={token}&limit=10")
        assert events_response.status_code == 200
        events = events_response.json()
        assert events

        event_id = events[0]["id"]
        detail_response = client.get(f"/api/v1/governance/events/{event_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()

        metadata = detail.get("metadata", {})
        assert metadata.get("notification_policy_scope_type") == "project"
        assert metadata.get("notification_policy_scope_id") == "proj_demo"
        assert metadata.get("notification_policy_event_type") == "notification_test"
        assert isinstance(metadata.get("fallback"), dict), "expected a fallback metadata dict for notification events"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        get_settings.cache_clear()

