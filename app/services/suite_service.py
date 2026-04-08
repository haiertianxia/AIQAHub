from uuid import uuid4

from sqlalchemy.orm import Session

from app.crud.suite import SuiteRepository
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

    def list_suites(self, db: Session) -> list[TestSuiteRead]:
        return [self._to_read(suite) for suite in self.repo.list(db)]

    def create_suite(self, db: Session, payload: TestSuiteCreate) -> TestSuiteRead:
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
