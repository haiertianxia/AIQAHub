from uuid import uuid4
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.crud.environment import EnvironmentRepository
from app.models.execution import Execution
from app.models.environment import Environment
from app.models.suite import TestSuite
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

    def list_environments(self, db: Session, *, project_id: str | None = None) -> list[EnvironmentRead]:
        statement = select(Environment).order_by(Environment.id.desc())
        if project_id is not None:
            statement = statement.where(Environment.project_id == project_id)
        return [self._to_read(env) for env in db.scalars(statement).all()]

    @staticmethod
    def _validate_base_url(base_url: str) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValidationError("base_url must use http or https")

    def get_environment(self, db: Session, env_id: str) -> EnvironmentRead:
        return self._to_read(self.repo.get(db, env_id))

    def create_environment(self, db: Session, payload: EnvironmentCreate) -> EnvironmentRead:
        self._validate_base_url(payload.base_url)
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

    def update_environment(self, db: Session, env_id: str, payload: EnvironmentCreate) -> EnvironmentRead:
        env = self.repo.get(db, env_id)
        if payload.project_id != env.project_id:
            raise ValidationError("project_id cannot be changed")
        self._validate_base_url(payload.base_url)
        env.project_id = payload.project_id
        env.name = payload.name
        env.env_type = payload.env_type
        env.base_url = payload.base_url
        env.credential_ref = payload.credential_ref
        env.db_ref = payload.db_ref
        db.commit()
        db.refresh(env)
        return self._to_read(env)

    def delete_environment(self, db: Session, env_id: str) -> EnvironmentRead:
        env = self.repo.get(db, env_id)
        has_execution = db.scalars(
            select(Execution.id).where(Execution.env_id == env.id).limit(1)
        ).first()
        has_suite_reference = db.scalars(
            select(TestSuite.id).where(TestSuite.default_env_id == env.id).limit(1)
        ).first()
        if has_execution is not None or has_suite_reference is not None:
            raise ValidationError("environment has execution or suite references and cannot be deleted")
        snapshot = self._to_read(env)
        db.delete(env)
        db.commit()
        return snapshot
