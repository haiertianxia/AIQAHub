from typing import Any

from app.orchestration.state_machine import ExecutionStateMachine
from app.workers.celery_app import celery_app


def _final_status_for_execution(execution_id: str) -> str:
    _ = execution_id
    return "success"


def _build_summary(final_status: str) -> dict[str, Any]:
    if final_status == "success":
        return {"passed": 1, "failed": 0, "success_rate": 100.0}
    if final_status == "failed":
        return {"passed": 0, "failed": 1, "success_rate": 0.0}
    raise ValueError(f"invalid final status: {final_status}")


@celery_app.task(name="aiqahub.execution.run")
def run_execution(execution_id: str) -> dict[str, Any]:
    state_machine = ExecutionStateMachine("queued")
    state_machine.mark_running()
    final_status = _final_status_for_execution(execution_id)
    if final_status == "success":
        state_machine.mark_success()
    elif final_status == "failed":
        state_machine.mark_failed()
    else:
        raise ValueError(f"invalid final status: {final_status}")

    return {
        "execution_id": execution_id,
        "status": state_machine.state,
        "summary": _build_summary(state_machine.state),
    }
