from app.orchestration.retry_policy import RetryPolicy
from app.orchestration.state_machine import ExecutionStateMachine
from app.orchestration.timeout_policy import TimeoutPolicy


class OrchestrationEngine:
    def __init__(self) -> None:
        self.retry_policy = RetryPolicy()
        self.timeout_policy = TimeoutPolicy()

    def create_state_machine(self) -> ExecutionStateMachine:
        return ExecutionStateMachine()

    def plan_execution(self, execution_id: str) -> dict[str, str]:
        return {"execution_id": execution_id, "status": "planned"}

