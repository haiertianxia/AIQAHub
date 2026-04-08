from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_execution_artifacts_and_timeline_are_available():
    execution_id = client.get("/api/v1/executions").json()[0]["id"]

    artifacts_response = client.get(f"/api/v1/executions/{execution_id}/artifacts")
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert artifacts, "expected at least one seeded artifact"

    timeline_response = client.get(f"/api/v1/executions/{execution_id}/timeline")
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    assert timeline, "expected a synthetic timeline"
