from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_settings_endpoint_returns_environment_summary():
    response = client.get("/api/v1/settings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"] == "AIQAHub"
    assert "database_url" in payload
    assert "redis_url" in payload


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
