from app.crud.base import Repository
from app.models.execution import Execution


class ExecutionRepository(Repository[Execution]):
    def __init__(self) -> None:
        super().__init__(Execution)

