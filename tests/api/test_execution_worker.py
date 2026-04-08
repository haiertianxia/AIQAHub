import pytest

from app.orchestration.engine import OrchestrationEngine
from app.workers.execution_tasks import run_execution


def test_plan_execution_queues_execution_and_dispatches_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    dispatched: list[str] = []

    class FakeAsyncResult:
        id = "task_123"

    def fake_delay(execution_id: str) -> FakeAsyncResult:
        dispatched.append(execution_id)
        return FakeAsyncResult()

    monkeypatch.setattr(run_execution, "delay", fake_delay)

    payload = OrchestrationEngine().plan_execution("exe_123")

    assert dispatched == ["exe_123"]
    assert payload == {
        "execution_id": "exe_123",
        "status": "queued",
        "task_id": "task_123",
    }


@pytest.mark.parametrize("final_status", ["success", "failed"])
def test_run_execution_returns_minimal_summary(final_status: str) -> None:
    payload = run_execution("exe_123", final_status=final_status)

    assert payload == {
        "execution_id": "exe_123",
        "status": final_status,
        "summary": {
            "execution_id": "exe_123",
            "status": final_status,
        },
    }
