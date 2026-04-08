from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.artifact import ExecutionArtifact
from app.models.execution import Execution
from app.schemas.report import ReportIndexItem, ReportSummary
from app.services.base import BaseService


class ReportService(BaseService):
    @staticmethod
    def _to_report(db: Session, execution: Execution) -> ReportSummary:
        artifacts = [
            {"name": artifact.name, "uri": artifact.storage_uri, "type": artifact.artifact_type}
            for artifact in db.scalars(select(ExecutionArtifact).where(ExecutionArtifact.execution_id == execution.id)).all()
        ]
        return ReportSummary(
            execution_id=execution.id,
            summary=execution.summary_json or {},
            artifacts=artifacts,
        )

    def list_reports(self, db: Session) -> list[ReportIndexItem]:
        executions = list(db.scalars(select(Execution)).all())
        return [
            ReportIndexItem(
                execution_id=execution.id,
                summary=self._to_report(db, execution).summary,
                artifacts=self._to_report(db, execution).artifacts,
                status=execution.status,
            )
            for execution in executions
        ]

    def get_report(self, db: Session, execution_id: str) -> ReportSummary:
        execution = db.get(Execution, execution_id)
        if execution is None:
            raise NotFoundError(f"Execution {execution_id} not found")
        return self._to_report(db, execution)
