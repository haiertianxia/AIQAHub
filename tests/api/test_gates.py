from fastapi.testclient import TestClient

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
