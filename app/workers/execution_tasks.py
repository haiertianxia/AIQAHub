from typing import Any

from app.orchestration.state_machine import ExecutionStateMachine
from app.workers.celery_app import celery_app


@celery_app.task(name="aiqahub.execution.run")
def run_execution(execution_id: str, final_status: str = "success") -> dict[str, Any]:
    state_machine = ExecutionStateMachine("queued")
    state_machine.mark_running()
    if final_status == "success":
        state_machine.mark_success()
    elif final_status == "failed":
        state_machine.mark_failed()
    else:
        raise ValueError(f"invalid final status: {final_status}")

    summary = {
        "execution_id": execution_id,
        "status": state_machine.state,
    }
    return {
        "execution_id": execution_id,
        "status": state_machine.state,
        "summary": summary,
    }
