from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import Repository
from app.models.artifact import ExecutionArtifact


class ExecutionArtifactRepository(Repository[ExecutionArtifact]):
    def __init__(self) -> None:
        super().__init__(ExecutionArtifact)

    def list_by_execution(self, db: Session, execution_id: str) -> list[ExecutionArtifact]:
        statement = select(self.model).where(self.model.execution_id == execution_id)
        return list(db.scalars(statement).all())
