import csv
from io import StringIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _csv_rows(response) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(response.text))
    return list(reader)


def test_shared_search_and_pagination_across_list_endpoints():
    token = f"query-contract-{uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/executions",
        json={
            "project_id": "proj_demo",
            "suite_id": "suite_demo",
            "env_id": "env_demo",
            "trigger_type": "manual",
            "trigger_source": token,
            "request_params": {"search_token": token},
        },
    )
    assert created.status_code == 200

    executions = client.get(f"/api/v1/executions?search={token}&page=1&page_size=1")
    reports = client.get(f"/api/v1/reports?search={token}&page=1&page_size=1")
    audit = client.get(f"/api/v1/audit?search={token}&page=1&page_size=1")

    ai_response = client.post(
        "/api/v1/ai/analyze",
        json={"input_text": f"{token} query for unified search", "context": {"execution_id": "exe_demo", "token": token}},
    )
    assert ai_response.status_code == 200
    ai_history = client.get(f"/api/v1/ai/history?search={token}&page=1&page_size=1")

    for response in (executions, reports, audit, ai_history):
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1

    assert executions.json()[0]["trigger_source"] == token
    assert reports.json()[0]["completion_source"] in {None, "trigger"}
    assert audit.json()[0]["action"] == "create_execution"
    assert ai_history.json()[0]["execution_id"] == "exe_demo"


def test_report_and_audit_exports_use_the_same_filters_as_list_endpoints():
    token = f"query-contract-export-{uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/executions",
        json={
            "project_id": "proj_demo",
            "suite_id": "suite_demo",
            "env_id": "env_demo",
            "trigger_type": "manual",
            "trigger_source": token,
            "request_params": {"export_token": token},
        },
    )
    assert created.status_code == 200

    report_list = client.get(f"/api/v1/reports?search={token}")
    report_export = client.get(f"/api/v1/reports/export?search={token}")
    audit_list = client.get(f"/api/v1/audit?search={token}")
    audit_export = client.get(f"/api/v1/audit/export?search={token}")

    assert report_list.status_code == 200
    assert report_export.status_code == 200
    assert audit_list.status_code == 200
    assert audit_export.status_code == 200

    report_rows = _csv_rows(report_export)
    audit_rows = _csv_rows(audit_export)

    assert report_rows and report_rows[0]["execution_id"] == report_list.json()[0]["execution_id"]
    assert audit_rows and audit_rows[0]["id"] == audit_list.json()[0]["id"]


def test_execution_search_uses_shared_query_contract():
    response = client.get("/api/v1/executions?search=exe_demo&page=1&page_size=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert any(item["id"] == "exe_demo" for item in payload)
