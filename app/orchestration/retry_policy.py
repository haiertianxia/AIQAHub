from dataclasses import dataclass


@dataclass(slots=True)
class RetryPolicy:
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    backoff_factor: float = 2.0

