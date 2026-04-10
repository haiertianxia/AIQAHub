from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.environment import Environment
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask

from app.main import app


client = TestClient(app)


def test_gate_rules_support_crud():
    created = client.post(
        "/api/v1/gates/rules",
        json={
            "project_id": "proj_demo",
            "name": "关键路径门禁",
            "rule_type": "critical_path",
            "enabled": True,
            "config": {"threshold": 95},
        },
    )

    assert created.status_code == 200
    rule = created.json()
    rule_id = rule["id"]

    listed = client.get("/api/v1/gates/rules")
    assert listed.status_code == 200
    assert any(item["id"] == rule_id for item in listed.json())

    updated = client.put(
        f"/api/v1/gates/rules/{rule_id}",
        json={
            "project_id": "proj_demo",
            "name": "关键路径门禁 V2",
            "rule_type": "critical_path",
            "enabled": False,
            "config": {"threshold": 98},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "关键路径门禁 V2"

    history = client.get(f"/api/v1/gates/rules/{rule_id}/history")
    assert history.status_code == 200
    history_items = history.json()
    assert history_items
    assert history_items[0]["rule_id"] == rule_id
    assert history_items[0]["action"] in {"create", "update"}

    deleted = client.delete(f"/api/v1/gates/rules/{rule_id}")
    assert deleted.status_code == 204


def test_scoped_rule_only_applies_to_matching_environment():
    baseline = client.post("/api/v1/gates/evaluate", json={"execution_id": "exe_demo"})
    assert baseline.status_code == 200
    baseline_result = baseline.json()["result"]

    project_id = f"proj_gate_scope_{uuid4().hex[:8]}"
    prod_env_id = f"env_{uuid4().hex[:8]}"
    prod_execution_id = f"exe_{uuid4().hex[:8]}"
    with SessionLocal() as db:
        db.add(
            Environment(
                id=prod_env_id,
                project_id=project_id,
                name="PROD",
                env_type="prod",
                base_url="https://prod.example.com",
                enabled=True,
            )
        )
        db.add(
            Execution(
                id=prod_execution_id,
                project_id=project_id,
                suite_id="suite_demo",
                env_id=prod_env_id,
                trigger_type="manual",
                trigger_source="ui",
                status="success",
                request_params_json={},
                summary_json={"passed": 3, "failed": 0, "success_rate": 96.7},
            )
        )
        for order, task_key in enumerate(["prepare", "execute", "collect"], start=1):
            db.add(
                ExecutionTask(
                    id=f"task_{uuid4().hex[:8]}",
                    execution_id=prod_execution_id,
                    task_key=task_key,
                    task_name=task_key.title(),
                    task_order=order,
                    status="success",
                    input_json={},
                    output_json={},
                )
            )
        db.commit()

    rule = client.post(
        "/api/v1/gates/rules",
        json={
            "project_id": project_id,
            "name": "Prod Only Gate",
            "rule_type": "success_rate",
            "enabled": True,
            "config": {
                "min_success_rate": 108,
                "min_task_count": 3,
                "scope": {"environment_types": ["prod"]},
            },
        },
    )
    assert rule.status_code == 200
    rule_id = rule.json()["id"]

    sit_result = client.post("/api/v1/gates/evaluate", json={"execution_id": "exe_demo"})
    assert sit_result.status_code == 200
    assert sit_result.json()["result"] == baseline_result

    prod_result = client.post("/api/v1/gates/evaluate", json={"execution_id": prod_execution_id})
    assert prod_result.status_code == 200
    payload = prod_result.json()
    assert payload["result"] == "FAIL"
    assert payload["completion_source"] == "unknown"

    client.delete(f"/api/v1/gates/rules/{rule_id}")
    with SessionLocal() as db:
        for task in db.query(ExecutionTask).filter(ExecutionTask.execution_id == prod_execution_id).all():
            db.delete(task)
        db.delete(db.get(Execution, prod_execution_id))
        db.delete(db.get(Environment, prod_env_id))
        db.commit()


def test_critical_task_keys_fail_when_missing():
    response = client.post(
        "/api/v1/gates/evaluate",
        json={"execution_id": "exe_demo"},
    )
    assert response.status_code == 200
    baseline = response.json()["result"]

    created = client.post(
        "/api/v1/gates/rules",
        json={
            "project_id": "proj_demo",
            "name": "Critical Smoke Gate",
            "rule_type": "success_rate",
            "enabled": True,
            "config": {
                "min_success_rate": 10,
                "min_task_count": 1,
                "critical_task_keys": ["smoke"],
            },
        },
    )
    assert created.status_code == 200
    rule_id = created.json()["id"]

    evaluated = client.post("/api/v1/gates/evaluate", json={"execution_id": "exe_demo"})
    assert evaluated.status_code == 200
    payload = evaluated.json()
    assert payload["result"] == "FAIL"
    assert "missing critical tasks" in payload["reason"]
    client.delete(f"/api/v1/gates/rules/{rule_id}")
