from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.artifact import ExecutionArtifact
from app.models.audit_log import AuditLog
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask
from app.utils.time import utcnow
from app.workers import execution_tasks
from app.workers.execution_tasks import wait_for_playwright


client = TestClient(app)


def test_execution_detail_exposes_raw_playwright_summary_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLAYWRIGHT_ENABLED", "1")
    monkeypatch.setenv("PLAYWRIGHT_COMMAND", "python3 -V")
    monkeypatch.setenv("PLAYWRIGHT_WORKDIR", "/tmp")
    get_settings.cache_clear()

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
                    "adapter": "playwright",
                    "job_name": "pw-regression",
                    "browser": "firefox",
                    "headless": False,
                    "base_url": "https://sit.example.com",
                },
                summary_json={},
            )
        )
        db.commit()

    execution_tasks.run_execution(execution_id)

    response = client.get(f"/api/v1/executions/{execution_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["playwright"]["job_name"] == "pw-regression"
    assert payload["summary"]["playwright"]["job_id"] == "playwright-pw-regression"
    assert payload["summary"]["playwright"]["status"] == "queued"
    assert payload["summary"]["playwright"]["completion_source"] == "trigger"
    assert payload["summary"]["playwright"]["poll_count"] == 0
    assert payload["summary"]["playwright"]["browser"] == "firefox"
    assert payload["summary"]["playwright"]["headless"] is False
    assert payload["summary"]["playwright"]["base_url"] == "https://sit.example.com"

    with SessionLocal() as db:
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all()
        artifacts = db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all()
        for artifact in artifacts:
            db.delete(artifact)
        for task in tasks:
            db.delete(task)
        execution = db.get(Execution, execution_id)
        if execution is not None:
            db.delete(execution)
        db.commit()
    get_settings.cache_clear()


def test_run_execution_uses_playwright_step_plan_and_required_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLAYWRIGHT_ENABLED", "1")
    monkeypatch.setenv("PLAYWRIGHT_COMMAND", "python3 -V")
    monkeypatch.setenv("PLAYWRIGHT_WORKDIR", "/tmp")
    get_settings.cache_clear()

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
                    "adapter": "playwright",
                    "job_name": "pw-regression",
                    "browser": "firefox",
                },
                summary_json={},
            )
        )
        db.commit()

    payload = execution_tasks.run_execution(execution_id)

    assert payload["execution_id"] == execution_id
    assert payload["status"] == "running"
    assert payload["summary"]["status"] == "running"
    assert payload["summary"]["passed"] == 1
    assert payload["summary"]["failed"] == 0
    assert payload["summary"]["success_rate"] == 100.0
    assert payload["summary"]["playwright"]["job_name"] == "pw-regression"
    assert payload["summary"]["playwright"]["job_id"] == "playwright-pw-regression"
    assert payload["summary"]["playwright"]["completion_source"] == "trigger"

    with SessionLocal() as db:
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all()
        assert [task.task_key for task in tasks] == ["trigger_playwright", "wait_for_playwright"]
        artifacts = db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all()
        artifact_types = sorted(artifact.artifact_type for artifact in artifacts)
        assert "playwright-junit" in artifact_types
        assert "playwright-html-report" in artifact_types
        for artifact in artifacts:
            db.delete(artifact)
        for task in tasks:
            db.delete(task)
        db.delete(db.get(Execution, execution_id))
        db.commit()
    get_settings.cache_clear()


def test_run_execution_fails_fast_when_playwright_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLAYWRIGHT_ENABLED", "0")
    monkeypatch.setenv("PLAYWRIGHT_COMMAND", "python3 -V")
    monkeypatch.setenv("PLAYWRIGHT_WORKDIR", "/tmp")
    get_settings.cache_clear()

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
                    "adapter": "playwright",
                    "job_name": "pw-regression",
                },
                summary_json={},
            )
        )
        db.commit()

    payload = execution_tasks.run_execution(execution_id)

    assert payload["execution_id"] == execution_id
    assert payload["status"] == "failed"
    assert payload["summary"]["status"] == "failed"
    assert payload["summary"]["completion_source"] == "validation"
    assert payload["summary"]["playwright"]["completion_source"] == "validation"
    assert payload["summary"]["playwright"]["status"] == "failed"

    with SessionLocal() as db:
        execution = db.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == "failed"
        assert execution.summary_json["playwright"]["status"] == "failed"
        tasks = db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all()
        assert [task.task_key for task in tasks] == ["trigger_playwright"]
        assert tasks[0].status == "failed"
        for task in tasks:
            db.delete(task)
        db.delete(execution)
        db.commit()
    get_settings.cache_clear()


def test_wait_for_playwright_polls_until_success() -> None:
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
                    "adapter": "playwright",
                    "job_name": "pw-regression",
                    "playwright_poll_sequence": ["running", "success"],
                },
                summary_json={
                    "status": "running",
                    "started_at": (utcnow() - timedelta(minutes=1)).isoformat(),
                    "playwright": {
                        "job_name": "pw-regression",
                        "job_id": "playwright-pw-regression",
                        "poll_count": 0,
                        "completion_source": "trigger",
                    },
                },
            )
        )
        task = ExecutionTask(
            id=f"task_{uuid4().hex[:12]}",
            execution_id=execution_id,
            task_key="wait_for_playwright",
            task_name="Wait For Playwright Run",
            task_order=2,
            status="running",
            input_json={"job_name": "pw-regression", "job_id": "playwright-pw-regression"},
            output_json={},
            error_message=None,
        )
        db.add(task)
        db.commit()
        task_id = task.id

    first = wait_for_playwright(execution_id, "pw-regression", "playwright-pw-regression", task_id, 0)
    assert first["status"] == "running"

    second = wait_for_playwright(execution_id, "pw-regression", "playwright-pw-regression", task_id, 1)
    assert second["status"] == "success"

    with SessionLocal() as db:
        execution = db.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == "success"
        assert execution.summary_json["playwright"]["completion_source"] == "poller_success"
        audit_rows = db.query(AuditLog).filter(AuditLog.target_id == execution_id).all()
        assert any(log.action == "playwright_completed" for log in audit_rows)
        task_row = db.get(ExecutionTask, task_id)
        assert task_row is not None
        assert task_row.status == "success"
        for artifact in db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all():
            db.delete(artifact)
        db.delete(task_row)
        db.delete(execution)
        db.commit()


def test_wait_for_playwright_exhausted_turns_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    class SettingsOverride:
        jenkins_poll_attempts = 1
        jenkins_poll_delay_seconds = 0

    monkeypatch.setattr(execution_tasks, "get_settings", lambda: SettingsOverride())

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
                    "adapter": "playwright",
                    "job_name": "pw-regression",
                    "playwright_poll_sequence": ["running"],
                },
                summary_json={
                    "status": "running",
                    "started_at": (utcnow() - timedelta(minutes=1)).isoformat(),
                    "playwright": {
                        "job_name": "pw-regression",
                        "job_id": "playwright-pw-regression",
                        "poll_count": 0,
                        "completion_source": "trigger",
                    },
                },
            )
        )
        task = ExecutionTask(
            id=f"task_{uuid4().hex[:12]}",
            execution_id=execution_id,
            task_key="wait_for_playwright",
            task_name="Wait For Playwright Run",
            task_order=2,
            status="running",
            input_json={"job_name": "pw-regression", "job_id": "playwright-pw-regression"},
            output_json={},
            error_message=None,
        )
        db.add(task)
        db.commit()
        task_id = task.id

    result = wait_for_playwright(execution_id, "pw-regression", "playwright-pw-regression", task_id, 0)
    assert result["status"] == "timeout"

    with SessionLocal() as db:
        execution = db.get(Execution, execution_id)
        assert execution is not None
        assert execution.status == "timeout"
        assert execution.summary_json["completion_source"] == "poller_exhausted"
        assert execution.summary_json["playwright"]["completion_source"] == "poller_exhausted"
        task_row = db.get(ExecutionTask, task_id)
        assert task_row is not None
        assert task_row.status == "timeout"
        for artifact in db.query(ExecutionArtifact).filter(ExecutionArtifact.execution_id == execution_id).all():
            db.delete(artifact)
        db.delete(task_row)
        db.delete(execution)
        db.commit()
