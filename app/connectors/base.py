from abc import ABC, abstractmethod


class Connector(ABC):
    @abstractmethod
    def test_connection(self) -> dict:
        raise NotImplementedError

