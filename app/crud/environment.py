from app.crud.base import Repository
from app.models.environment import Environment


class EnvironmentRepository(Repository[Environment]):
    def __init__(self) -> None:
        super().__init__(Environment)

