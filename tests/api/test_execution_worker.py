import pytest
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.execution import Execution
from app.orchestration.engine import OrchestrationEngine
from app.schemas.execution import ExecutionCreate
from app.services.execution_service import ExecutionService
from app.workers import execution_tasks


def test_plan_execution_queues_execution_and_dispatches_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    dispatched: list[str] = []

    class FakeAsyncResult:
        id = "task_123"

    def fake_delay(execution_id: str) -> FakeAsyncResult:
        dispatched.append(execution_id)
        return FakeAsyncResult()

    monkeypatch.setattr(execution_tasks.run_execution, "delay", fake_delay)

    payload = OrchestrationEngine().plan_execution("exe_123")

    assert dispatched == ["exe_123"]
    assert payload == {
        "execution_id": "exe_123",
        "status": "queued",
        "summary": {
            "execution_id": "exe_123",
            "status": "queued",
        },
    }


def test_run_execution_returns_minimal_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    execution_id = f"exe_{uuid4().hex[:12]}"
    with SessionLocal() as db:
        db.add(
            Execution(
                id=execution_id,
                project_id="proj_demo",
                suite_id="suite_demo",
                env_id="env_demo",
                trigger_type="manual",
                trigger_source="ui",
                status="queued",
                request_params_json={},
                summary_json={},
            )
        )
        db.commit()

    payload = execution_tasks.run_execution(execution_id)

    assert payload == {
        "execution_id": execution_id,
        "status": "success",
        "summary": {
            "passed": 1,
            "failed": 0,
            "success_rate": 100.0,
        },
    }

    with SessionLocal() as db:
        db.delete(db.get(Execution, execution_id))
        db.commit()


def test_run_execution_reports_failed_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(execution_tasks, "_final_status_for_execution", lambda _: "failed")

    execution_id = f"exe_{uuid4().hex[:12]}"
    with SessionLocal() as db:
        db.add(
            Execution(
                id=execution_id,
                project_id="proj_demo",
                suite_id="suite_demo",
                env_id="env_demo",
                trigger_type="manual",
                trigger_source="ui",
                status="queued",
                request_params_json={},
                summary_json={},
            )
        )
        db.commit()

    payload = execution_tasks.run_execution(execution_id)

    assert payload == {
        "execution_id": execution_id,
        "status": "failed",
        "summary": {
            "passed": 0,
            "failed": 1,
            "success_rate": 0.0,
        },
    }

    with SessionLocal() as db:
        db.delete(db.get(Execution, execution_id))
        db.commit()


def test_execution_run_updates_state_and_summary() -> None:
    service = ExecutionService()
    payload = ExecutionCreate(
        project_id="proj_demo",
        suite_id="suite_demo",
        env_id="env_demo",
        trigger_type="manual",
        trigger_source="test",
        request_params={"branch": "task-2"},
    )

    with SessionLocal() as db:
        created = service.create_execution(db, payload)

    execution_tasks.run_execution(created.id)

    with SessionLocal() as db:
        execution = db.get(Execution, created.id)
        assert execution is not None
        assert execution.status == "success"
        assert execution.summary_json == {
            "passed": 1,
            "failed": 0,
            "success_rate": 100.0,
        }
        db.delete(execution)
        db.commit()
