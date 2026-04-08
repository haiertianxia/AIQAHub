from typing import Any

from app.orchestration.retry_policy import RetryPolicy
from app.orchestration.state_machine import ExecutionStateMachine
from app.orchestration.timeout_policy import TimeoutPolicy
from app.workers.execution_tasks import run_execution


class OrchestrationEngine:
    def __init__(self) -> None:
        self.retry_policy = RetryPolicy()
        self.timeout_policy = TimeoutPolicy()

    def create_state_machine(self) -> ExecutionStateMachine:
        return ExecutionStateMachine()

    def queue_execution(self, execution_id: str) -> dict[str, Any]:
        state_machine = self.create_state_machine()
        state_machine.mark_queued()
        async_result = run_execution.delay(execution_id)
        return {
            "execution_id": execution_id,
            "status": state_machine.state,
            "task_id": async_result.id,
        }

    def plan_execution(self, execution_id: str) -> dict[str, Any]:
        return self.queue_execution(execution_id)
