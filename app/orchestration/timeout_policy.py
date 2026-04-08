from dataclasses import dataclass


@dataclass(slots=True)
class TimeoutPolicy:
    timeout_seconds: int = 3600

