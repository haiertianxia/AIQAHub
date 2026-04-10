from fastapi.testclient import TestClient
from uuid import uuid4

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
