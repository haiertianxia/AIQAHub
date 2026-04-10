from abc import ABC, abstractmethod


class Connector(ABC):
    allowed_statuses = {"created", "queued", "running", "success", "failed", "timeout", "canceled"}

    @abstractmethod
    def validate_config(self) -> dict:
        raise NotImplementedError

    def test_connection(self) -> dict:
        return self.validate_config()

    @classmethod
    def normalize_status(cls, value: str | None, default: str = "created") -> str:
        status = (value or default).strip().lower()
        return status if status in cls.allowed_statuses else default
