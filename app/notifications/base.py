from abc import ABC, abstractmethod
from typing import Any


class NotificationProvider(ABC):
    channel: str

    @abstractmethod
    def send(
        self,
        *,
        message: str,
        subject: str | None = None,
        target: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

