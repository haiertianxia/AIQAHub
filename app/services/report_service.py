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
        summary = execution.summary_json or {}
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
            status=execution.status,
            summary=summary,
            artifacts=artifacts,
            tasks=tasks,
            task_count=len(tasks),
            completion_source=summary.get("completion_source"),
            completed_at=summary.get("completed_at"),
            started_at=summary.get("started_at"),
        )

    def list_reports(
        self,
        db: Session,
        *,
        search: str | None = None,
        status: str | None = None,
        completion_source: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[ReportIndexItem]:
        executions = list(db.scalars(select(Execution)).all())
        if search:
            lowered = search.lower()
            executions = [execution for execution in executions if lowered in execution.id.lower()]
        if status:
            executions = [execution for execution in executions if execution.status == status]
        if completion_source:
            executions = [
                execution
                for execution in executions
                if str((execution.summary_json or {}).get("completion_source") or "").lower() == completion_source.lower()
            ]
        start = max(page - 1, 0) * page_size
        end = start + page_size
        executions = executions[start:end]
        reports: list[ReportIndexItem] = []
        for execution in executions:
            report = self._to_report(db, execution)
            reports.append(
                ReportIndexItem(
                    execution_id=report.execution_id,
                    status=report.status,
                    summary=report.summary,
                    artifacts=report.artifacts,
                    tasks=report.tasks,
                    task_count=report.task_count,
                    completion_source=report.completion_source,
                    completed_at=report.completed_at,
                    started_at=report.started_at,
                )
            )
        return reports

    def get_report(self, db: Session, execution_id: str) -> ReportSummary:
        execution = db.get(Execution, execution_id)
        if execution is None:
            raise NotFoundError(f"Execution {execution_id} not found")
        return self._to_report(db, execution)

    def export_reports_csv(
        self,
        db: Session,
        *,
        search: str | None = None,
        status: str | None = None,
        completion_source: str | None = None,
    ) -> str:
        reports = self.list_reports(db, search=search, status=status, completion_source=completion_source, page=1, page_size=1000)
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["execution_id", "status", "completion_source", "task_count", "passed", "failed", "success_rate"])
        for report in reports:
            writer.writerow(
                [
                    report.execution_id,
                    report.status,
                    report.completion_source or "",
                    report.task_count,
                    report.summary.get("passed", 0),
                    report.summary.get("failed", 0),
                    report.summary.get("success_rate", 0),
                ]
            )
        return buffer.getvalue()
from io import StringIO
import csv
