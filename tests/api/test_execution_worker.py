import pytest

from app.orchestration.engine import OrchestrationEngine
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
    payload = execution_tasks.run_execution("exe_123")

    assert payload == {
        "execution_id": "exe_123",
        "status": "success",
        "summary": {
            "passed": 1,
            "failed": 0,
            "success_rate": 100.0,
        },
    }


def test_run_execution_reports_failed_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(execution_tasks, "_final_status_for_execution", lambda _: "failed")

    payload = execution_tasks.run_execution("exe_123")

    assert payload == {
        "execution_id": "exe_123",
        "status": "failed",
        "summary": {
            "passed": 0,
            "failed": 1,
            "success_rate": 0.0,
        },
    }
