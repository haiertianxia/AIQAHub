from io import StringIO
import csv

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.artifact import ExecutionArtifact
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask
from app.schemas.query import ExportQueryParams, ListQueryParams
from app.schemas.report import ReportIndexItem, ReportSummary
from app.services.base import BaseService
from app.services.query_filters import (
    apply_case_insensitive_filter,
    apply_contains_filter,
    apply_json_path_filter,
    apply_pagination,
    apply_sort,
)


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

    def _base_statement(self):
        statement = select(Execution)
        return statement

    def _apply_filters(self, statement, query: ListQueryParams | ExportQueryParams):
        statement = apply_case_insensitive_filter(statement, Execution.status, query.status)
        statement = apply_json_path_filter(statement, Execution.summary_json, "$.completion_source", query.completion_source)
        statement = apply_contains_filter(
            statement,
            [
                Execution.id,
                Execution.project_id,
                Execution.suite_id,
                Execution.env_id,
                Execution.trigger_type,
                Execution.trigger_source,
                Execution.error_message,
                Execution.summary_json,
            ],
            query.search,
        )
        statement = apply_sort(
            statement,
            sort=query.sort,
            allowed={
                "id": Execution.id,
                "status": Execution.status,
                "project_id": Execution.project_id,
                "suite_id": Execution.suite_id,
                "env_id": Execution.env_id,
                "trigger_type": Execution.trigger_type,
                "completion_source": func.coalesce(func.json_extract(Execution.summary_json, "$.completion_source"), ""),
            },
            default="-id",
        )
        return statement

    def list_reports(self, db: Session, *, query: ListQueryParams) -> list[ReportIndexItem]:
        statement = self._apply_filters(self._base_statement(), query)
        statement = apply_pagination(statement, page=query.page, page_size=query.page_size)
        executions = list(db.scalars(statement).all())
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

    def export_reports_csv(self, db: Session, *, query: ExportQueryParams) -> str:
        statement = self._apply_filters(self._base_statement(), query)
        reports = [self._to_report(db, execution) for execution in db.scalars(statement).all()]
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
