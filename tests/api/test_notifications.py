import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.execution_task import ExecutionTask
from app.schemas.execution import ExecutionCreate
from app.schemas.gate import GateEvaluateRequest
from app.main import app
from app.services.execution_service import ExecutionService
from app.services.gate_service import GateService


client = TestClient(app)


def test_settings_endpoint_supports_notification_updates():
    environment = f"qa_notify_{uuid4().hex[:8]}"
    response = client.put(
        f"/api/v1/settings?environment={environment}",
        json={
            "app_name": "AIQAHub",
            "app_version": "1.2.3",
            "log_level": "INFO",
            "jenkins_url": "https://jenkins.example.com",
            "jenkins_user": "qa-bot",
            "notification_default_channel": "dingtalk",
            "notification_email_enabled": True,
            "notification_email_smtp_host": "smtp.example.com",
            "notification_email_smtp_port": 2525,
            "notification_email_from": "qa@example.com",
            "notification_email_to": "ops@example.com",
            "notification_dingtalk_enabled": True,
            "notification_dingtalk_webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=test",
            "notification_wecom_enabled": True,
            "notification_wecom_webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["notification_default_channel"] == "dingtalk"
    assert payload["notification_email_enabled"] is True
    assert payload["notification_email_to"] == "ops@example.com"
    assert payload["notification_dingtalk_enabled"] is True
    assert payload["notification_wecom_enabled"] is True

    history_response = client.get(f"/api/v1/settings/history?environment={environment}")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history
    assert history[0]["notification_default_channel"] == "dingtalk"
    assert history[0]["notification_email_enabled"] is True


def test_notification_test_endpoint_posts_to_webhook_channel():
    received: dict[str, object] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
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
    environment = f"qa_notify_{uuid4().hex[:8]}"
    try:
        client.put(
            f"/api/v1/settings?environment={environment}",
            json={
                "notification_default_channel": "dingtalk",
                "notification_dingtalk_enabled": True,
                "notification_dingtalk_webhook_url": f"http://127.0.0.1:{server.server_port}/robot/send",
            },
        )
        response = client.post(
            f"/api/v1/notifications/test?environment={environment}",
            json={
                "channel": "dingtalk",
                "subject": "Build failed",
                "message": "execution exe_demo failed",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["channel"] == "dingtalk"
        assert payload["status"] == "success"
        assert received["path"] == "/robot/send"
        assert received["payload"]["msgtype"] == "text"
        assert "execution exe_demo failed" in received["payload"]["text"]["content"]
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_failed_execution_triggers_notification_webhook(monkeypatch):
    received: dict[str, object] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
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
    environment = f"qa_notify_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    try:
        update_response = client.put(
            f"/api/v1/settings?environment={environment}",
            json={
                "notification_default_channel": "dingtalk",
                "notification_dingtalk_enabled": True,
                "notification_dingtalk_webhook_url": f"http://127.0.0.1:{server.server_port}/notify",
            },
        )
        assert update_response.status_code == 200

        service = ExecutionService()
        with SessionLocal() as db:
            created = service.create_execution(
                db,
                ExecutionCreate(
                    project_id="proj_demo",
                    suite_id="suite_demo",
                    env_id="env_demo",
                    request_params={},
                ),
            )
            service.mark_running(db, created.id)
            service.mark_completed(
                db,
                created.id,
                status="failed",
                summary={"passed": 0, "failed": 1, "success_rate": 0.0},
            )

        assert received["path"] == "/notify"
        assert received["payload"]["msgtype"] == "text"
        assert "execution" in received["payload"]["text"]["content"].lower()
    finally:
        server.shutdown()
        thread.join(timeout=2)
        get_settings.cache_clear()


def test_gate_failure_triggers_notification_webhook(monkeypatch):
    received: dict[str, object] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
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
    environment = f"qa_gate_{uuid4().hex[:8]}"
    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()

    try:
        update_response = client.put(
            f"/api/v1/settings?environment={environment}",
            json={
                "notification_default_channel": "dingtalk",
                "notification_dingtalk_enabled": True,
                "notification_dingtalk_webhook_url": f"http://127.0.0.1:{server.server_port}/gate",
            },
        )
        assert update_response.status_code == 200

        service = ExecutionService()
        gate_service = GateService()
        with SessionLocal() as db:
            created = service.create_execution(
                db,
                ExecutionCreate(
                    project_id="proj_demo",
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
        assert received["path"] == "/gate"
        assert received["payload"]["msgtype"] == "text"
        assert "gate" in received["payload"]["text"]["content"].lower()
    finally:
        server.shutdown()
        thread.join(timeout=2)
        get_settings.cache_clear()
