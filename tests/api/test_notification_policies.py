import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from uuid import uuid4

import pytest
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.schemas.execution import ExecutionCreate
from app.schemas.gate import GateEvaluateRequest
from app.services.execution_service import ExecutionService
from app.services.gate_service import GateService
from app.services.settings_service import SettingsService


@pytest.fixture(autouse=True)
def isolated_settings_store(monkeypatch, tmp_path):
    monkeypatch.setattr(SettingsService, "overrides_path", tmp_path / "settings_overrides.json")
    monkeypatch.setattr(SettingsService, "history_path", tmp_path / "settings_history.json")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _client():
    from fastapi.testclient import TestClient

    return TestClient(app)


def _start_webhook_server() -> tuple[HTTPServer, threading.Thread, dict[str, object]]:
    received: dict[str, object] = {"count": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            received["count"] = int(received["count"]) + 1
            received["path"] = self.path
            received["payload"] = json.loads(body)
            encoded = json.dumps({"ok": True}).encode("utf-8")
            self.send_response(200)
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


def _start_failing_webhook_server() -> tuple[HTTPServer, threading.Thread, dict[str, object]]:
    received: dict[str, object] = {"count": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            received["count"] = int(received["count"]) + 1
            received["path"] = self.path
            received["payload"] = json.loads(body)
            encoded = json.dumps({"ok": False, "error": "forced failure"}).encode("utf-8")
            self.send_response(500)
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


def _inject_notification_config(
    environment: str,
    overrides_path: Path,
    *,
    default_channel: str,
    dingtalk_url: str,
    wecom_url: str,
) -> None:
    payload: dict[str, object] = {"environments": {}}
    if overrides_path.exists():
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    environments = payload.setdefault("environments", {})
    env_payload = environments.setdefault(environment, {})
    env_payload["notification_default_channel"] = default_channel
    env_payload["notification_dingtalk_enabled"] = True
    env_payload["notification_dingtalk_webhook_url"] = dingtalk_url
    env_payload["notification_wecom_enabled"] = True
    env_payload["notification_wecom_webhook_url"] = wecom_url
    overrides_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def _inject_notification_policies(environment: str, overrides_path: Path, policies: list[dict[str, object]]) -> None:
    payload: dict[str, object] = {"environments": {}}
    if overrides_path.exists():
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    environments = payload.setdefault("environments", {})
    env_payload = environments.setdefault(environment, {})
    env_payload["notification_policies"] = policies
    overrides_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def _policy(
    *,
    scope_type: str,
    scope_id: str,
    event_type: str,
    channel: str,
    target: str,
    enabled: bool = True,
) -> dict[str, object]:
    return {
        "scope_type": scope_type,
        "scope_id": scope_id,
        "event_type": event_type,
        "enabled": enabled,
        "channels": [channel],
        "target": target,
    }


def _create_failed_execution(project_id: str) -> str:
    service = ExecutionService()
    with SessionLocal() as db:
        created = service.create_execution(
            db,
            ExecutionCreate(
                project_id=project_id,
                suite_id="suite_demo",
                env_id="env_demo",
                request_params={},
            ),
        )
        service.mark_running(db, created.id)
        completed = service.mark_completed(
            db,
            created.id,
            status="failed",
            summary={"passed": 0, "failed": 1, "success_rate": 0.0},
        )
    return completed.id


def _create_failed_gate_result(project_id: str) -> str:
    service = ExecutionService()
    gate_service = GateService()
    with SessionLocal() as db:
        created = service.create_execution(
            db,
            ExecutionCreate(
                project_id=project_id,
                suite_id="suite_demo",
                env_id="env_demo",
                request_params={},
            ),
        )
        task = service.create_task(
            db,
            execution_id=created.id,
            task_key="execute",
            task_name="Execute",
            task_order=1,
            input_json={},
        )
        service.update_task_status(db, task.id, status="failed", output_json={"reason": "boom"})
        result = gate_service.evaluate(db, GateEvaluateRequest(execution_id=created.id))
    assert result.result == "FAIL"
    return created.id


def test_project_policy_overrides_global_default_policy(monkeypatch, tmp_path):
    environment = f"qa_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    global_server, global_thread, global_received = _start_webhook_server()
    project_server, project_thread, project_received = _start_webhook_server()
    try:
        client = _client()
        _inject_notification_config(
            environment,
            tmp_path / "settings_overrides.json",
            default_channel="dingtalk",
            dingtalk_url=_webhook_url(global_server, "/global"),
            wecom_url=_webhook_url(project_server, "/project"),
        )
        _inject_notification_policies(
            environment,
            tmp_path / "settings_overrides.json",
            [
                _policy(
                    scope_type="global",
                    scope_id="",
                    event_type="execution_failed",
                    channel="dingtalk",
                    target=_webhook_url(global_server, "/global"),
                ),
                _policy(
                    scope_type="project",
                    scope_id="proj_demo",
                    event_type="execution_failed",
                    channel="wecom",
                    target=_webhook_url(project_server, "/project"),
                ),
            ],
        )

        _create_failed_execution("proj_demo")

        assert project_received["count"] == 1
        assert project_received["path"] == "/project"
        assert global_received["count"] == 0
    finally:
        global_server.shutdown()
        project_server.shutdown()
        global_thread.join(timeout=2)
        project_thread.join(timeout=2)


def test_global_default_policy_is_used_when_no_project_policy_exists(monkeypatch, tmp_path):
    environment = f"qa_notify_{uuid4().hex[:8]}"
    project_id = f"proj_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    global_server, global_thread, global_received = _start_webhook_server()
    fallback_server, fallback_thread, fallback_received = _start_webhook_server()
    try:
        client = _client()
        _inject_notification_config(
            environment,
            tmp_path / "settings_overrides.json",
            default_channel="wecom",
            dingtalk_url=_webhook_url(global_server, "/global"),
            wecom_url=_webhook_url(fallback_server, "/fallback"),
        )
        _inject_notification_policies(
            environment,
            tmp_path / "settings_overrides.json",
            [
                _policy(
                    scope_type="global",
                    scope_id="",
                    event_type="execution_failed",
                    channel="dingtalk",
                    target=_webhook_url(global_server, "/global"),
                ),
            ],
        )

        _create_failed_execution(project_id)

        assert global_received["count"] == 1
        assert global_received["path"] == "/global"
        assert fallback_received["count"] == 0
    finally:
        global_server.shutdown()
        fallback_server.shutdown()
        global_thread.join(timeout=2)
        fallback_thread.join(timeout=2)


def test_disabled_policy_is_skipped(monkeypatch, tmp_path):
    environment = f"qa_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    global_server, global_thread, global_received = _start_webhook_server()
    disabled_server, disabled_thread, disabled_received = _start_webhook_server()
    try:
        client = _client()
        _inject_notification_config(
            environment,
            tmp_path / "settings_overrides.json",
            default_channel="wecom",
            dingtalk_url=_webhook_url(global_server, "/global"),
            wecom_url=_webhook_url(disabled_server, "/disabled"),
        )
        _inject_notification_policies(
            environment,
            tmp_path / "settings_overrides.json",
            [
                _policy(
                    scope_type="global",
                    scope_id="",
                    event_type="execution_failed",
                    channel="dingtalk",
                    target=_webhook_url(global_server, "/global"),
                ),
                _policy(
                    scope_type="project",
                    scope_id="proj_demo",
                    event_type="execution_failed",
                    channel="wecom",
                    target=_webhook_url(disabled_server, "/disabled"),
                    enabled=False,
                ),
            ],
        )

        _create_failed_execution("proj_demo")

        assert global_received["count"] == 1
        assert global_received["path"] == "/global"
        assert disabled_received["count"] == 0
    finally:
        global_server.shutdown()
        disabled_server.shutdown()
        global_thread.join(timeout=2)
        disabled_thread.join(timeout=2)


def test_notification_failures_do_not_break_execution_or_gate_completion(monkeypatch, tmp_path):
    environment = f"qa_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    global_server, global_thread, global_received = _start_webhook_server()
    project_server, project_thread, project_received = _start_failing_webhook_server()
    try:
        client = _client()
        _inject_notification_config(
            environment,
            tmp_path / "settings_overrides.json",
            default_channel="dingtalk",
            dingtalk_url=_webhook_url(global_server, "/global"),
            wecom_url=_webhook_url(project_server, "/project"),
        )
        _inject_notification_policies(
            environment,
            tmp_path / "settings_overrides.json",
            [
                _policy(
                    scope_type="project",
                    scope_id="proj_demo",
                    event_type="execution_failed",
                    channel="wecom",
                    target=_webhook_url(project_server, "/project"),
                ),
                _policy(
                    scope_type="project",
                    scope_id="proj_demo",
                    event_type="gate_failed",
                    channel="wecom",
                    target=_webhook_url(project_server, "/project"),
                ),
            ],
        )

        execution_service = ExecutionService()
        with SessionLocal() as db:
            created = execution_service.create_execution(
                db,
                ExecutionCreate(
                    project_id="proj_demo",
                    suite_id="suite_demo",
                    env_id="env_demo",
                    request_params={},
                ),
            )
            execution_service.mark_running(db, created.id)
            completed = execution_service.mark_completed(
                db,
                created.id,
                status="failed",
                summary={"passed": 0, "failed": 1, "success_rate": 0.0},
            )

        gate_execution_id = _create_failed_gate_result("proj_demo")

        assert completed.status == "failed"
        assert gate_execution_id
        assert project_received["count"] == 2
        assert project_received["path"] == "/project"
        assert global_received["count"] == 0
    finally:
        global_server.shutdown()
        project_server.shutdown()
        global_thread.join(timeout=2)
        project_thread.join(timeout=2)


def test_notification_test_endpoint_uses_selected_channel_and_target(monkeypatch, tmp_path):
    environment = f"qa_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    global_server, global_thread, global_received = _start_webhook_server()
    project_server, project_thread, project_received = _start_webhook_server()
    try:
        client = _client()
        _inject_notification_config(
            environment,
            tmp_path / "settings_overrides.json",
            default_channel="dingtalk",
            dingtalk_url=_webhook_url(global_server, "/global"),
            wecom_url=_webhook_url(project_server, "/project"),
        )
        _inject_notification_policies(
            environment,
            tmp_path / "settings_overrides.json",
            [
                _policy(
                    scope_type="global",
                    scope_id="",
                    event_type="notification_test",
                    channel="dingtalk",
                    target=_webhook_url(global_server, "/global"),
                ),
                _policy(
                    scope_type="project",
                    scope_id="proj_demo",
                    event_type="notification_test",
                    channel="wecom",
                    target=_webhook_url(project_server, "/project"),
                ),
            ],
        )

        response = client.post(
            f"/api/v1/notifications/test?environment={environment}",
            json={
                "message": "policy routing check",
                "channel": "dingtalk",
                "target": _webhook_url(global_server, "/global"),
                "project_id": "proj_demo",
                "event_type": "notification_test",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["channel"] == "wecom"
        assert payload["target"] == _webhook_url(project_server, "/project")
        assert project_received["count"] == 1
        assert project_received["path"] == "/project"
        assert global_received["count"] == 0
    finally:
        global_server.shutdown()
        project_server.shutdown()
        global_thread.join(timeout=2)
        project_thread.join(timeout=2)
