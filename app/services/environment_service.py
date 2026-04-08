from uuid import uuid4

from sqlalchemy.orm import Session

from app.crud.environment import EnvironmentRepository
from app.models.environment import Environment
from app.schemas.environment import EnvironmentCreate, EnvironmentRead
from app.services.base import BaseService


class EnvironmentService(BaseService):
    def __init__(self) -> None:
        self.repo = EnvironmentRepository()

    @staticmethod
    def _to_read(env: Environment) -> EnvironmentRead:
        return EnvironmentRead(
            id=env.id,
            project_id=env.project_id,
            name=env.name,
            env_type=env.env_type,
            base_url=env.base_url,
            credential_ref=env.credential_ref,
            db_ref=env.db_ref,
            enabled=env.enabled,
        )

    def list_environments(self, db: Session) -> list[EnvironmentRead]:
        return [self._to_read(env) for env in self.repo.list(db)]

    def create_environment(self, db: Session, payload: EnvironmentCreate) -> EnvironmentRead:
        env = Environment(
            id=f"env_{uuid4().hex[:12]}",
            project_id=payload.project_id,
            name=payload.name,
            env_type=payload.env_type,
            base_url=payload.base_url,
            credential_ref=payload.credential_ref,
            db_ref=payload.db_ref,
        )
        self.repo.add(db, env)
        return EnvironmentRead(
            id=env.id,
            project_id=env.project_id,
            name=env.name,
            env_type=env.env_type,
            base_url=env.base_url,
            credential_ref=env.credential_ref,
            db_ref=env.db_ref,
            enabled=env.enabled,
        )
