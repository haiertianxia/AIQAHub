from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_reports_list_includes_seeded_execution():
    response = client.get("/api/v1/reports")
    assert response.status_code == 200

    reports = response.json()
    assert reports, "expected seeded report entries"

    first = reports[0]
    assert "execution_id" in first
    assert "summary" in first
    assert "artifacts" in first


def test_report_detail_matches_execution_id():
    execution_id = client.get("/api/v1/executions").json()[0]["id"]
    response = client.get(f"/api/v1/reports/{execution_id}")

    assert response.status_code == 200
    payload = response.json()

    assert payload["execution_id"] == execution_id
    assert "summary" in payload
