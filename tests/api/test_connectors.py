from fastapi.testclient import TestClient

from app.connectors.jenkins.client import JenkinsConnector
from app.core.config import get_settings
from app.main import app


client = TestClient(app)


def test_list_connectors_includes_jenkins():
    response = client.get("/api/v1/connectors")

    assert response.status_code == 200
    connectors = response.json()
    assert any(connector["connector_type"] == "jenkins" and connector["status"] == "success" for connector in connectors)


def test_test_jenkins_connector_returns_status():
    response = client.post(
        "/api/v1/connectors/jenkins/test",
        json={
            "payload": {
                "base_url": "https://jenkins.example.com",
                "username": "demo",
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["connector_type"] == "jenkins"
    assert body["ok"] is True
    assert body["status"] == "success"


def test_jenkins_connector_normalizes_execution_statuses():
    connector = JenkinsConnector(base_url="https://jenkins.example.com", username="demo")

    trigger = connector.trigger_job("webchat-regression")
    running = connector.get_build_status("webchat-regression", 42, final_status="RUNNING")
    success = connector.get_build_status("webchat-regression", 42, final_status="SUCCESS")

    assert trigger["status"] == "queued"
    assert running["status"] == "running"
    assert success["status"] == "success"


def test_test_playwright_connector_fails_when_disabled(monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_ENABLED", "0")
    monkeypatch.setenv("PLAYWRIGHT_COMMAND", "npx playwright test")
    monkeypatch.setenv("PLAYWRIGHT_WORKDIR", "/tmp")
    get_settings.cache_clear()
    try:
        response = client.post("/api/v1/connectors/playwright/test", json={"payload": {}})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["connector_type"] == "playwright"
    assert body["ok"] is False
    assert body["status"] == "failed"
    assert "disabled" in body["message"].lower()


def test_test_playwright_connector_fails_when_required_settings_missing(monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_ENABLED", "1")
    monkeypatch.setenv("PLAYWRIGHT_COMMAND", "")
    monkeypatch.setenv("PLAYWRIGHT_WORKDIR", "")
    get_settings.cache_clear()
    try:
        response = client.post("/api/v1/connectors/playwright/test", json={"payload": {}})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["connector_type"] == "playwright"
    assert body["ok"] is False
    assert body["status"] == "failed"
    assert "missing" in body["message"].lower()
    assert body["details"]["missing"] == ["playwright_command", "playwright_workdir"]


def test_test_playwright_connector_returns_runnable_job_handle(monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_ENABLED", "1")
    monkeypatch.setenv("PLAYWRIGHT_COMMAND", "npx playwright test")
    monkeypatch.setenv("PLAYWRIGHT_WORKDIR", "/tmp")
    monkeypatch.setenv("PLAYWRIGHT_DEFAULT_BASE_URL", "https://example.test")
    monkeypatch.setenv("PLAYWRIGHT_DEFAULT_BROWSER", "chromium")
    monkeypatch.setenv("PLAYWRIGHT_DEFAULT_HEADLESS", "1")
    get_settings.cache_clear()
    try:
        response = client.post(
            "/api/v1/connectors/playwright/test",
            json={"payload": {"job_name": "smoke", "browser": "firefox", "headless": False}},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["connector_type"] == "playwright"
    assert body["ok"] is True
    assert body["status"] == "queued"
    assert body["details"]["job_name"] == "smoke"
    assert body["details"]["command"] == "npx playwright test"
    assert body["details"]["workdir"] == "/tmp"
    assert body["details"]["browser"] == "firefox"
    assert body["details"]["headless"] is False
