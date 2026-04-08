from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_reports_list_returns_seeded_execution_reports():
    response = client.get("/api/v1/reports")

    assert response.status_code == 200
    reports = response.json()
    assert reports, "expected at least one seeded report"
    assert reports[0]["execution_id"]
    assert "summary" in reports[0]
    assert "artifacts" in reports[0]


def test_gate_rules_can_be_created_and_listed():
    create_response = client.post(
        "/api/v1/gates/rules",
        json={
            "project_id": "proj_seed",
            "name": "关键路径成功率",
            "rule_type": "success_rate",
            "enabled": True,
            "config": {"min_success_rate": 95},
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["name"] == "关键路径成功率"
    assert created["project_id"] == "proj_seed"

    list_response = client.get("/api/v1/gates/rules")
    assert list_response.status_code == 200
    rules = list_response.json()
    assert any(rule["id"] == created["id"] for rule in rules)


def test_gate_evaluation_uses_seeded_execution():
    executions = client.get("/api/v1/executions").json()
    execution_id = executions[0]["id"]

    response = client.post("/api/v1/gates/evaluate", json={"execution_id": execution_id})

    assert response.status_code == 200
    result = response.json()
    assert result["execution_id"] == execution_id
    assert result["result"] in {"PASS", "WARN", "FAIL"}


def test_execution_detail_exposes_timeline_and_artifacts():
    execution_id = client.get("/api/v1/executions").json()[0]["id"]

    artifacts_response = client.get(f"/api/v1/executions/{execution_id}/artifacts")
    timeline_response = client.get(f"/api/v1/executions/{execution_id}/timeline")

    assert artifacts_response.status_code == 200
    assert timeline_response.status_code == 200
    assert isinstance(artifacts_response.json(), list)
    assert isinstance(timeline_response.json(), list)
