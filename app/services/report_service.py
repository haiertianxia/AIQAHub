from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.artifact import ExecutionArtifact
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask
from app.schemas.report import ReportIndexItem, ReportSummary
from app.services.base import BaseService


class ReportService(BaseService):
    @staticmethod
    def _to_report(db: Session, execution: Execution) -> ReportSummary:
        artifacts = [
            {"name": artifact.name, "uri": artifact.storage_uri, "type": artifact.artifact_type}
            for artifact in db.scalars(select(ExecutionArtifact).where(ExecutionArtifact.execution_id == execution.id)).all()
        ]
        tasks = [
            {
                "id": task.id,
                "task_key": task.task_key,
                "task_name": task.task_name,
                "status": task.status,
                "output": task.output_json or {},
            }
            for task in db.scalars(select(ExecutionTask).where(ExecutionTask.execution_id == execution.id)).all()
        ]
        return ReportSummary(
            execution_id=execution.id,
            summary=execution.summary_json or {},
            artifacts=artifacts,
            tasks=tasks,
            task_count=len(tasks),
        )

    def list_reports(self, db: Session) -> list[ReportIndexItem]:
        executions = list(db.scalars(select(Execution)).all())
        reports: list[ReportIndexItem] = []
        for execution in executions:
            report = self._to_report(db, execution)
            reports.append(
                ReportIndexItem(
                    execution_id=report.execution_id,
                    summary=report.summary,
                    artifacts=report.artifacts,
                    tasks=report.tasks,
                    task_count=report.task_count,
                    status=execution.status,
                )
            )
        return reports

    def get_report(self, db: Session, execution_id: str) -> ReportSummary:
        execution = db.get(Execution, execution_id)
        if execution is None:
            raise NotFoundError(f"Execution {execution_id} not found")
        return self._to_report(db, execution)
