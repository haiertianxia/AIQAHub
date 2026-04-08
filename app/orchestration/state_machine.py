from dataclasses import dataclass


VALID_TRANSITIONS: dict[str, set[str]] = {
    "created": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"success", "failed", "cancelled", "timeout"},
    "failed": {"queued", "cancelled"},
    "success": set(),
    "cancelled": set(),
    "timeout": set(),
}


@dataclass(slots=True)
class ExecutionStateMachine:
    state: str = "created"

    def can_transition(self, next_state: str) -> bool:
        return next_state in VALID_TRANSITIONS.get(self.state, set())

    def transition(self, next_state: str) -> None:
        if not self.can_transition(next_state):
            raise ValueError(f"invalid transition: {self.state} -> {next_state}")
        self.state = next_state

