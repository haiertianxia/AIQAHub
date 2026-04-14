import json
import threading
from contextlib import contextmanager
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


@contextmanager
def _notification_test_context(monkeypatch, *, default_channel: str = "dingtalk", policies: list[dict[str, object]] | None = None):
    environment = f"qa_gov_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    dingtalk_server, dingtalk_thread, dingtalk_received = _start_webhook_server()
    wecom_server, wecom_thread, wecom_received = _start_webhook_server()
    client = _client()
    try:
        _configure_notification_settings(
            client,
            environment=environment,
            default_channel=default_channel,
            dingtalk_url=_webhook_url(dingtalk_server, "/dingtalk"),
            wecom_url=_webhook_url(wecom_server, "/wecom"),
            policies=policies,
        )
        yield client, environment, {
            "dingtalk": dingtalk_received,
            "wecom": wecom_received,
            "dingtalk_url": _webhook_url(dingtalk_server, "/dingtalk"),
            "wecom_url": _webhook_url(wecom_server, "/wecom"),
        }
    finally:
        client.close()
        dingtalk_server.shutdown()
        dingtalk_thread.join(timeout=2)
        dingtalk_server.server_close()
        wecom_server.shutdown()
        wecom_thread.join(timeout=2)
        wecom_server.server_close()
        get_settings.cache_clear()


def test_notification_sends_appear_in_governance_overview(monkeypatch):
    """
    Required behavior:
    1. Notification sends appear in governance overview or event stream.

    This test asserts that notification sends are reflected in governance overview
    counters and appear in the governance event stream.
    """

    token = f"gov_notify_token_{uuid4().hex}"
    with _notification_test_context(monkeypatch) as (client, _environment, received):
        send_response = client.post(
            f"/api/v1/notifications/test?environment={_environment}",
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
        assert received["dingtalk"]["count"] == 1

        overview_response = client.get("/api/v1/governance/overview")
        assert overview_response.status_code == 200
        overview = overview_response.json()
        assert overview.get("notification_send_count", 0) >= 1

        events_response = client.get(f"/api/v1/governance/events?search={token}&page=1&page_size=50")
        assert events_response.status_code == 200
        events = events_response.json()

        notification_events = [event for event in events if event.get("kind") == "notification_test"]
        assert notification_events, "expected governance events to include notification_test items"


def test_notification_events_are_filterable_by_kind_and_channel(monkeypatch):
    """
    Required behavior:
    2. Notification events are filterable by kind and channel.

    This test checks that the governance event stream can distinguish notification
    kinds and channels independently.
    """

    with _notification_test_context(monkeypatch) as (client, environment, _received):
        dingtalk_token = f"gov_notify_dingtalk_{uuid4().hex}"
        wecom_token = f"gov_notify_wecom_{uuid4().hex}"

        first_response = client.post(
            f"/api/v1/notifications/test?environment={environment}",
            json={
                "channel": "dingtalk",
                "subject": "Governance notification filter test",
                "message": f"notification send token={dingtalk_token}",
                "metadata": {"test_token": dingtalk_token},
                "event_type": "notification_test",
                "project_id": "proj_demo",
            },
        )
        assert first_response.status_code == 200

        second_response = client.post(
            f"/api/v1/notifications/test?environment={environment}",
            json={
                "channel": "wecom",
                "subject": "Governance notification filter test",
                "message": f"notification send token={wecom_token}",
                "metadata": {"test_token": wecom_token},
                "event_type": "notification_skip",
                "project_id": "proj_demo",
            },
        )
        assert second_response.status_code == 200

        dingtalk_events_response = client.get(
            "/api/v1/governance/events?kind=notification_test&channel=dingtalk&page=1&page_size=50"
        )
        assert dingtalk_events_response.status_code == 200
        dingtalk_events = dingtalk_events_response.json()
        assert dingtalk_events
        assert all(event.get("kind") == "notification_test" and event.get("channel") == "dingtalk" for event in dingtalk_events)

        dingtalk_provider_response = client.get(
            "/api/v1/governance/events?kind=notification_test&provider=dingtalk&page=1&page_size=50"
        )
        assert dingtalk_provider_response.status_code == 200
        dingtalk_provider_events = dingtalk_provider_response.json()
        assert dingtalk_provider_events
        assert all(event.get("kind") == "notification_test" and event.get("provider") == "dingtalk" for event in dingtalk_provider_events)

        wecom_events_response = client.get(
            "/api/v1/governance/events?kind=notification_skip&channel=wecom&page=1&page_size=50"
        )
        assert wecom_events_response.status_code == 200
        wecom_events = wecom_events_response.json()
        assert wecom_events
        assert all(event.get("kind") == "notification_skip" and event.get("channel") == "wecom" for event in wecom_events)

        send_events_response = client.get(
            "/api/v1/governance/events?kind=notification_skip&provider=wecom&page=1&page_size=50"
        )
        assert send_events_response.status_code == 200
        send_events = send_events_response.json()
        assert send_events
        assert all(event.get("kind") == "notification_skip" and event.get("provider") == "wecom" for event in send_events)


def test_notification_event_detail_includes_policy_and_fallback_metadata(monkeypatch):
    """
    Required behavior:
    3. Notification event detail includes policy and fallback metadata.

    The "policy" metadata is expected to align with NotificationPolicyService routing keys.
    The "fallback" metadata is required even when no fallback is used.
    """

    token = f"gov_notify_token_{uuid4().hex}"
    with _notification_test_context(
        monkeypatch,
        default_channel="wecom",
        policies=[
            {
                "scope_type": "project",
                "scope_id": "proj_demo",
                "event_type": "notification_test",
                "enabled": True,
                "channels": ["dingtalk"],
                "subject_template": "Policy routed {event_type} ({project_id})",
                "filters": {"project_id": ["proj_demo"]},
            }
        ],
    ) as (client, _environment, _received):
        send_response = client.post(
            f"/api/v1/notifications/test?environment={_environment}",
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

        events_response = client.get(f"/api/v1/governance/events?search={token}&page=1&page_size=10")
        assert events_response.status_code == 200
        events = events_response.json()
        assert events

        matching_event = next((event for event in events if event.get("metadata", {}).get("test_token") == token), None)
        assert matching_event is not None

        event_id = matching_event["id"]
        detail_response = client.get(f"/api/v1/governance/events/{event_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()

        assert detail.get("policy_scope_type") == "project"
        assert detail.get("policy_scope_id") == "proj_demo"
        assert detail.get("channel") == "dingtalk"
        assert detail.get("provider") == "dingtalk"
        assert "fallback_from" in detail
        assert "fallback_reason" in detail
        assert isinstance(detail.get("raw"), dict)

        raw_response = detail["raw"].get("response_json", {})
        assert raw_response.get("channel") == "dingtalk"
        assert raw_response.get("provider") == "dingtalk"
        assert raw_response.get("target")
        assert raw_response.get("metadata", {}).get("notification_policy_scope_type") == "project"
        assert raw_response.get("metadata", {}).get("notification_policy_scope_id") == "proj_demo"
        assert raw_response.get("metadata", {}).get("notification_policy_event_type") == "notification_test"
