import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from fastapi.testclient import TestClient
from uuid import uuid4

from app.core.config import get_settings
from app.main import app


client = TestClient(app)


def test_settings_endpoint_returns_environment_summary():
    response = client.get("/api/v1/settings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"] == "AIQAHub"
    assert "database_url" in payload
    assert "redis_url" in payload


def test_settings_endpoint_supports_updates():
    environment = f"qa_test_{uuid4().hex[:8]}"
    update_response = client.put(
        f"/api/v1/settings?environment={environment}",
        json={
            "app_name": "AIQAHub-Updated",
            "app_version": "9.9.9",
            "log_level": "DEBUG",
            "jenkins_url": "https://jenkins.example.com",
            "jenkins_user": "qa-bot",
        },
    )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["environment"] == environment
    assert payload["app_name"] == "AIQAHub-Updated"
    assert payload["app_version"] == "9.9.9"
    assert payload["log_level"] == "DEBUG"
    assert payload["jenkins_url"] == "https://jenkins.example.com"
    assert payload["jenkins_user"] == "qa-bot"
    history_response = client.get(f"/api/v1/settings/history?environment={environment}")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history
    assert history[0]["environment"] == environment
    assert history[0]["app_name"] == "AIQAHub-Updated"
    assert history[0]["action"] == "update"


def test_settings_endpoint_supports_rollback():
    environment = f"qa_test_{uuid4().hex[:8]}"
    first_response = client.put(
        f"/api/v1/settings?environment={environment}",
        json={
            "app_name": "AIQAHub-Rollback-1",
            "app_version": "1.0.1",
            "log_level": "INFO",
            "jenkins_url": "https://jenkins-a.example.com",
            "jenkins_user": "qa-one",
        },
    )
    assert first_response.status_code == 200
    initial_revision = first_response.json()["revision_number"]

    second_response = client.put(
        f"/api/v1/settings?environment={environment}",
        json={
            "app_name": "AIQAHub-Rollback-2",
            "app_version": "1.0.2",
            "log_level": "DEBUG",
            "jenkins_url": "https://jenkins-b.example.com",
            "jenkins_user": "qa-two",
        },
    )
    assert second_response.status_code == 200

    rollback_response = client.post(
        "/api/v1/settings/rollback",
        json={
            "environment": environment,
            "revision_number": initial_revision,
        },
    )
    assert rollback_response.status_code == 200
    rolled_back = rollback_response.json()
    assert rolled_back["environment"] == environment
    assert rolled_back["app_name"] == "AIQAHub-Rollback-1"
    assert rolled_back["app_version"] == "1.0.1"
    assert rolled_back["jenkins_user"] == "qa-one"

    history_response = client.get(f"/api/v1/settings/history?environment={environment}")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history[0]["action"] == "rollback"
    assert history[0]["app_name"] == "AIQAHub-Rollback-1"
    assert history[1]["action"] == "update"


def test_audit_logs_are_listed_from_persisted_data():
    response = client.get("/api/v1/audit")

    assert response.status_code == 200
    logs = response.json()
    assert logs, "expected seeded audit logs"
    assert logs[0]["action"]


def test_audit_overview_combines_governance_sources():
    response = client.get("/api/v1/audit/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["audit_log_count"] >= 1
    assert payload["settings_revision_count"] >= 1
    assert payload["asset_revision_count"] >= 1
    assert payload["connector_count"] >= 1
    assert payload["connectors"]
    assert payload["recent_audit_logs"]
    assert payload["recent_settings_history"]
    assert payload["recent_asset_revisions"]


def test_ai_analyze_returns_result_payload():
    response = client.post(
        "/api/v1/ai/analyze",
        json={"input_text": "登录失败回归", "context": {"project": "proj_demo"}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"]
    assert payload["result"]["summary"]
    assert payload["result"]["suggestions"]


def test_ai_analyze_uses_configured_provider_and_model(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "rule-based")
    monkeypatch.setenv("AI_MODEL_NAME", "qa-llm")
    get_settings.cache_clear()
    try:
        response = client.post(
            "/api/v1/ai/analyze",
            json={"input_text": "登录失败回归", "context": {"project": "proj_demo"}},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["model"] == "qa-llm"
        assert payload["result"]["provider"] == "rule-based"
        assert payload["result"]["model"] == "qa-llm"
    finally:
        get_settings.cache_clear()


def test_ai_analyze_can_use_openai_compatible_provider(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body)
            assert payload["model"] == "qa-openai"
            assert payload["messages"][1]["role"] == "user"
            response = {
                "choices": [
                    {
                        "message": {
                            "content": "openai-compatible summary",
                        }
                    }
                ]
            }
            encoded = json.dumps(response).encode("utf-8")
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
    try:
        monkeypatch.setenv("AI_PROVIDER", "openai")
        monkeypatch.setenv("AI_MODEL_NAME", "qa-openai")
        monkeypatch.setenv("OPENAI_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        get_settings.cache_clear()

        response = client.post(
            "/api/v1/ai/analyze",
            json={"input_text": "登录失败回归", "context": {"project": "proj_demo"}},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["model"] == "qa-openai"
        assert payload["result"]["provider"] == "openai"
        assert payload["result"]["summary"] == "openai-compatible summary"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        get_settings.cache_clear()


def test_ai_analyze_falls_back_to_mock_when_openai_provider_fails(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            payload = json.dumps({"error": "provider failure"}).encode("utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv("AI_PROVIDER", "openai")
        monkeypatch.setenv("AI_MODEL_NAME", "qa-openai")
        monkeypatch.setenv("OPENAI_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        get_settings.cache_clear()

        response = client.post(
            "/api/v1/ai/analyze",
            json={"input_text": "登录失败回归", "context": {"project": "proj_demo"}},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["model"] == "qa-openai"
        assert payload["result"]["provider"] == "mock"
        assert payload["result"]["fallback_from"] == "openai"
        assert payload["result"]["fallback_reason"]

        overview = client.get("/api/v1/governance/overview")
        assert overview.status_code == 200
        overview_payload = overview.json()
        assert overview_payload["ai_provider"] == "openai"
        assert overview_payload["ai_model_name"] == "qa-openai"
        assert overview_payload["ai_fallback_count"] >= 1
    finally:
        server.shutdown()
        thread.join(timeout=2)
        get_settings.cache_clear()
