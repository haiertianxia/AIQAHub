from abc import ABC, abstractmethod


class Connector(ABC):
    @abstractmethod
    def validate_config(self) -> dict:
        raise NotImplementedError

    def test_connection(self) -> dict:
        return self.validate_config()
