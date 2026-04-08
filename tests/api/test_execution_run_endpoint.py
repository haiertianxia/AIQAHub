from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.execution import Execution
from app.main import app
from app.orchestration.engine import OrchestrationEngine
from app.schemas.execution import ExecutionCreate
from app.services.execution_service import ExecutionService


client = TestClient(app)


def test_execution_run_endpoint_dispatches_worker(monkeypatch):
    service = ExecutionService()
    payload = ExecutionCreate(
        project_id="proj_demo",
        suite_id="suite_demo",
        env_id="env_demo",
        trigger_type="manual",
        trigger_source="ui",
        request_params={"branch": "main"},
    )
    with SessionLocal() as db:
        created = service.create_execution(db, payload)

    def fake_queue_execution(self, queued_execution_id: str):
        return {
            "execution_id": queued_execution_id,
            "status": "queued",
            "task_id": "task_123",
            "summary": {"execution_id": queued_execution_id, "status": "queued"},
        }

    monkeypatch.setattr(OrchestrationEngine, "queue_execution", fake_queue_execution)

    response = client.post(f"/api/v1/executions/{created.id}/run")

    assert response.status_code == 200
    assert response.json() == {
        "execution_id": created.id,
        "status": "queued",
        "task_id": "task_123",
        "summary": {"execution_id": created.id, "status": "queued"},
    }

    with SessionLocal() as db:
        execution = db.get(Execution, created.id)
        assert execution is not None
        db.delete(execution)
        db.commit()


def test_execution_run_endpoint_rejects_terminal_execution():
    response = client.post("/api/v1/executions/exe_demo/run")

    assert response.status_code == 400
    assert response.json()["detail"] == "execution must be queued before running"
