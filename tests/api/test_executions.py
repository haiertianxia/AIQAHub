from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_execution_detail_returns_execution_payload():
    executions_response = client.get("/api/v1/executions")
    assert executions_response.status_code == 200

    executions = executions_response.json()
    assert executions, "expected seeded executions for detail lookup"

    execution_id = executions[0]["id"]
    detail_response = client.get(f"/api/v1/executions/{execution_id}")

    assert detail_response.status_code == 200
    payload = detail_response.json()

    assert payload["id"] == execution_id
    assert payload["status"] == executions[0]["status"]
    assert payload["summary"] == executions[0]["summary"]


def test_execution_artifacts_and_timeline_are_available():
    executions_response = client.get("/api/v1/executions")
    execution_id = executions_response.json()[0]["id"]

    artifacts_response = client.get(f"/api/v1/executions/{execution_id}/artifacts")
    timeline_response = client.get(f"/api/v1/executions/{execution_id}/timeline")

    assert artifacts_response.status_code == 200
    assert timeline_response.status_code == 200
    assert isinstance(artifacts_response.json(), list)
    assert isinstance(timeline_response.json(), list)
