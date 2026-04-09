import pytest
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.artifact import ExecutionArtifact
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask
from app.orchestration.engine import OrchestrationEngine
from app.schemas.execution import ExecutionCreate
from app.services.execution_service import ExecutionService
from app.workers import execution_tasks


client = TestClient(app)


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
        "task_id": "task_123",
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
            "passed": 3,
            "failed": 0,
            "success_rate": 100.0,
        },
    }

    with SessionLocal() as db:
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all()
        artifacts = db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all()
        assert [task.task_key for task in tasks] == ["prepare", "execute", "collect"]
        assert all(task.status == "success" for task in tasks)
        assert len(artifacts) == 3
        for artifact in artifacts:
            db.delete(artifact)
        for task in tasks:
            db.delete(task)
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
            "passed": 2,
            "failed": 1,
            "success_rate": 66.7,
        },
    }

    with SessionLocal() as db:
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all()
        assert [task.status for task in tasks] == ["success", "success", "failed"]
        for artifact in db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all():
            db.delete(artifact)
        for task in tasks:
            db.delete(task)
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
            "passed": 3,
            "failed": 0,
            "success_rate": 100.0,
        }
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == created.id).all()
        assert len(tasks) == 3
        artifacts = db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == created.id).all()
        assert len(artifacts) == 3
        for artifact in artifacts:
            db.delete(artifact)
        for task in tasks:
            db.delete(task)
        db.delete(execution)
        db.commit()


def test_run_execution_uses_custom_step_plan() -> None:
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
                request_params_json={
                    "steps": [
                        {"task_key": "bootstrap", "task_name": "Bootstrap"},
                        {"task_key": "smoke", "task_name": "Smoke"},
                    ]
                },
                summary_json={},
            )
        )
        db.commit()

    execution_tasks.run_execution(execution_id)

    with SessionLocal() as db:
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all()
        assert [task.task_key for task in tasks] == ["bootstrap", "smoke"]
        assert [task.task_name for task in tasks] == ["Bootstrap", "Smoke"]
        execution = db.get(Execution, execution_id)
        assert execution is not None
        assert execution.summary_json == {
            "passed": 2,
            "failed": 0,
            "success_rate": 100.0,
        }
        for artifact in db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all():
            db.delete(artifact)
        for task in tasks:
            db.delete(task)
        db.delete(execution)
        db.commit()


def test_run_execution_uses_jenkins_step_plan() -> None:
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
                request_params_json={
                    "adapter": "jenkins",
                    "job_name": "webchat-regression",
                },
                summary_json={},
            )
        )
        db.commit()

    payload = execution_tasks.run_execution(execution_id)

    assert payload["execution_id"] == execution_id
    assert payload["status"] == "running"
    assert payload["task_id"]
    assert payload["summary"] == {
        "status": "running",
        "passed": 1,
        "failed": 0,
        "success_rate": 100.0,
        "jenkins": {
            "job_name": "webchat-regression",
            "build_number": 42,
            "queue_id": "queue_webchat-regression",
            "build_url": "job/webchat-regression/42",
        },
    }

    with SessionLocal() as db:
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all()
        assert [task.task_key for task in tasks] == ["trigger_job"]
        artifacts = db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all()
        assert len(artifacts) == 1
        for artifact in artifacts:
            db.delete(artifact)
        for task in tasks:
            db.delete(task)
        db.delete(db.get(Execution, execution_id))
        db.commit()


def test_jenkins_callback_finalizes_execution() -> None:
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
                status="running",
                request_params_json={"adapter": "jenkins", "job_name": "webchat-regression"},
                summary_json={
                    "status": "running",
                    "passed": 1,
                    "failed": 0,
                    "success_rate": 100.0,
                    "jenkins": {
                        "job_name": "webchat-regression",
                        "build_number": 42,
                        "queue_id": "queue_webchat-regression",
                        "build_url": "job/webchat-regression/42",
                    },
                },
            )
        )
        db.add(
            ExecutionTask(
                id=f"task_{uuid4().hex[:12]}",
                execution_id=execution_id,
                task_key="trigger_job",
                task_name="Trigger Jenkins Job",
                task_order=1,
                status="success",
                input_json={"job_name": "webchat-regression"},
                output_json={"build_number": 42, "build_url": "job/webchat-regression/42"},
                error_message=None,
            )
        )
        db.commit()

    response = client.post(
        "/api/v1/connectors/jenkins/callback",
        json={
            "execution_id": execution_id,
            "job_name": "webchat-regression",
            "build_number": 42,
            "result": "success",
            "build_url": "https://jenkins.example.com/job/webchat-regression/42/",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["summary"]["jenkins"]["build_number"] == 42

    with SessionLocal() as db:
        execution = db.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == "success"
        assert execution.summary_json["jenkins"]["result"] == "success"
        for task in db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all():
            db.delete(task)
        db.delete(execution)
        db.commit()
