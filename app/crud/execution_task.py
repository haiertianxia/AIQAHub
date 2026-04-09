from app.crud.base import Repository
from app.models.execution_task import ExecutionTask


class ExecutionTaskRepository(Repository[ExecutionTask]):
    def __init__(self) -> None:
        super().__init__(ExecutionTask)
