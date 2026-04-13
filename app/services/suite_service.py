from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.crud.suite import SuiteRepository
from app.models.environment import Environment
from app.models.execution import Execution
from app.models.suite import TestSuite
from app.schemas.suite import TestSuiteCreate, TestSuiteRead
from app.services.base import BaseService


class SuiteService(BaseService):
    def __init__(self) -> None:
        self.repo = SuiteRepository()

    @staticmethod
    def _to_read(suite: TestSuite) -> TestSuiteRead:
        return TestSuiteRead(
            id=suite.id,
            project_id=suite.project_id,
            name=suite.name,
            suite_type=suite.suite_type,
            source_type=suite.source_type,
            source_ref=suite.source_ref,
            default_env_id=suite.default_env_id,
        )

    def list_suites(self, db: Session, *, project_id: str | None = None) -> list[TestSuiteRead]:
        statement = select(TestSuite).order_by(TestSuite.id.desc())
        if project_id is not None:
            statement = statement.where(TestSuite.project_id == project_id)
        return [self._to_read(suite) for suite in db.scalars(statement).all()]

    def _validate_default_environment(self, db: Session, payload: TestSuiteCreate) -> None:
        if payload.default_env_id is None:
            return
        default_env = db.get(Environment, payload.default_env_id)
        if default_env is None:
            raise ValidationError("default environment not found")
        if default_env.project_id != payload.project_id:
            raise ValidationError("default environment must belong to the same project")

    def get_suite(self, db: Session, suite_id: str) -> TestSuiteRead:
        return self._to_read(self.repo.get(db, suite_id))

    def create_suite(self, db: Session, payload: TestSuiteCreate) -> TestSuiteRead:
        self._validate_default_environment(db, payload)
        suite = TestSuite(
            id=f"suite_{uuid4().hex[:12]}",
            project_id=payload.project_id,
            name=payload.name,
            suite_type=payload.suite_type,
            source_type=payload.source_type,
            source_ref=payload.source_ref,
            default_env_id=payload.default_env_id,
        )
        self.repo.add(db, suite)
        return TestSuiteRead(
            id=suite.id,
            project_id=suite.project_id,
            name=suite.name,
            suite_type=suite.suite_type,
            source_type=suite.source_type,
            source_ref=suite.source_ref,
            default_env_id=suite.default_env_id,
        )

    def update_suite(self, db: Session, suite_id: str, payload: TestSuiteCreate) -> TestSuiteRead:
        suite = self.repo.get(db, suite_id)
        if payload.project_id != suite.project_id:
            raise ValidationError("project_id cannot be changed")
        self._validate_default_environment(db, payload)
        suite.project_id = payload.project_id
        suite.name = payload.name
        suite.suite_type = payload.suite_type
        suite.source_type = payload.source_type
        suite.source_ref = payload.source_ref
        suite.default_env_id = payload.default_env_id
        db.commit()
        db.refresh(suite)
        return self._to_read(suite)

    def delete_suite(self, db: Session, suite_id: str) -> TestSuiteRead:
        suite = self.repo.get(db, suite_id)
        has_execution = db.scalars(
            select(Execution.id).where(Execution.suite_id == suite.id).limit(1)
        ).first()
        if has_execution is not None:
            raise ValidationError("suite has executions")
        snapshot = self._to_read(suite)
        db.delete(suite)
        db.commit()
        return snapshot
