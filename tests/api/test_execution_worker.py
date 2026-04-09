import pytest
import json
import time
from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.db.session import SessionLocal
from app.models.artifact import ExecutionArtifact
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask
from app.orchestration.engine import OrchestrationEngine
from app.schemas.execution import ExecutionCreate
from app.services.execution_service import ExecutionService
from app.services.webhook_security import compute_jenkins_webhook_signature
from app.workers import execution_tasks
from app.workers.execution_tasks import sweep_stale_executions, wait_for_jenkins_build
from app.utils.time import utcnow


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
        assert execution.summary_json["passed"] == 3
        assert execution.summary_json["failed"] == 0
        assert execution.summary_json["success_rate"] == 100.0
        assert "completed_at" in execution.summary_json
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
        assert execution.summary_json["passed"] == 2
        assert execution.summary_json["failed"] == 0
        assert execution.summary_json["success_rate"] == 100.0
        assert "completed_at" in execution.summary_json
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
            "completion_source": "trigger",
            "poll_count": 0,
        },
        "started_at": payload["summary"]["started_at"],
    }

    with SessionLocal() as db:
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all()
        assert [task.task_key for task in tasks] == ["trigger_job", "wait_for_build"]
        artifacts = db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all()
        assert len(artifacts) == 1
        for artifact in artifacts:
            db.delete(artifact)
        for task in tasks:
            db.delete(task)
        db.delete(db.get(Execution, execution_id))
        db.commit()


def test_wait_for_jenkins_build_polls_until_success(monkeypatch: pytest.MonkeyPatch) -> None:
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
                request_params_json={
                    "adapter": "jenkins",
                    "job_name": "webchat-regression",
                    "jenkins_poll_sequence": ["running", "success"],
                },
                summary_json={
                    "status": "running",
                    "started_at": (utcnow() - timedelta(minutes=1)).isoformat(),
                    "jenkins": {
                        "job_name": "webchat-regression",
                        "build_number": 42,
                        "queue_id": "queue_webchat-regression",
                        "build_url": "job/webchat-regression/42",
                        "poll_count": 0,
                        "completion_source": "trigger",
                    },
                },
            )
        )
        task = ExecutionTask(
            id=f"task_{uuid4().hex[:12]}",
            execution_id=execution_id,
            task_key="wait_for_build",
            task_name="Wait For Jenkins Build",
            task_order=2,
            status="running",
            input_json={"job_name": "webchat-regression", "build_number": 42},
            output_json={},
            error_message=None,
        )
        db.add(task)
        db.commit()
        task_id = task.id

    first = wait_for_jenkins_build(execution_id, "webchat-regression", 42, "job/webchat-regression/42", task_id, 0)
    assert first["status"] == "running"

    second = wait_for_jenkins_build(execution_id, "webchat-regression", 42, "job/webchat-regression/42", task_id, 1)
    assert second["status"] == "success"

    with SessionLocal() as db:
        execution = db.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == "success"
        assert execution.summary_json["jenkins"]["completion_source"] == "poller_success"
        task_row = db.get(ExecutionTask, task_id)
        assert task_row is not None
        assert task_row.status == "success"
        for artifact in db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all():
            db.delete(artifact)
        db.delete(task_row)
        db.delete(execution)
        db.commit()


def test_wait_for_jenkins_build_exhausted_turns_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    class SettingsOverride:
        jenkins_poll_attempts = 1
        jenkins_poll_delay_seconds = 0

    monkeypatch.setattr(execution_tasks, "get_settings", lambda: SettingsOverride())
    monkeypatch.setattr("app.services.connector_service.get_settings", lambda: SettingsOverride())

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
                request_params_json={
                    "adapter": "jenkins",
                    "job_name": "webchat-regression",
                    "jenkins_poll_sequence": ["running"],
                },
                summary_json={
                    "status": "running",
                    "started_at": (utcnow() - timedelta(minutes=1)).isoformat(),
                    "jenkins": {
                        "job_name": "webchat-regression",
                        "build_number": 42,
                        "queue_id": "queue_webchat-regression",
                        "build_url": "job/webchat-regression/42",
                        "poll_count": 0,
                        "completion_source": "trigger",
                    },
                },
            )
        )
        task = ExecutionTask(
            id=f"task_{uuid4().hex[:12]}",
            execution_id=execution_id,
            task_key="wait_for_build",
            task_name="Wait For Jenkins Build",
            task_order=2,
            status="running",
            input_json={"job_name": "webchat-regression", "build_number": 42},
            output_json={},
            error_message=None,
        )
        db.add(task)
        db.commit()
        task_id = task.id

    result = wait_for_jenkins_build(execution_id, "webchat-regression", 42, "job/webchat-regression/42", task_id, 0)
    assert result["status"] == "timeout"

    with SessionLocal() as db:
        execution = db.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == "timeout"
        assert execution.summary_json["completion_source"] == "poller_exhausted"
        task_row = db.get(ExecutionTask, task_id)
        assert task_row is not None
        assert task_row.status == "timeout"
        for artifact in db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all():
            db.delete(artifact)
        db.delete(task_row)
        db.delete(execution)
        db.commit()


def test_sweep_stale_executions_times_out_running_execution() -> None:
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
                request_params_json={},
                summary_json={
                    "status": "running",
                    "started_at": (utcnow() - timedelta(hours=2)).isoformat(),
                    "passed": 1,
                    "failed": 0,
                    "success_rate": 100.0,
                },
            )
        )
        db.add(
            ExecutionTask(
                id=f"task_{uuid4().hex[:12]}",
                execution_id=execution_id,
                task_key="collect",
                task_name="Collect Artifacts",
                task_order=3,
                status="running",
                input_json={},
                output_json={},
                error_message=None,
            )
        )
        db.commit()

    result = sweep_stale_executions()
    assert execution_id in result["timed_out"]

    with SessionLocal() as db:
        execution = db.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == "timeout"
        assert execution.summary_json["status"] == "timeout"
        task_row = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).one()
        assert task_row.status == "timeout"
        db.delete(task_row)
        db.delete(execution)
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

    payload = {
        "execution_id": execution_id,
        "job_name": "webchat-regression",
        "build_number": 42,
        "result": "success",
        "build_url": "https://jenkins.example.com/job/webchat-regression/42/",
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    nonce = f"nonce_{uuid4().hex}"
    signature = compute_jenkins_webhook_signature(
        secret=get_settings().jenkins_webhook_secret,
        timestamp=timestamp,
        nonce=nonce,
        execution_id=execution_id,
        body=body,
    )
    response = client.post(
        "/api/v1/connectors/jenkins/callback",
        content=body,
        headers={
            "X-AIQA-Timestamp": timestamp,
            "X-AIQA-Nonce": nonce,
            "X-AIQA-Signature": signature,
            "X-AIQA-Execution-Id": execution_id,
            "Content-Type": "application/json",
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
