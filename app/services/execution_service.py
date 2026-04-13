from uuid import uuid4

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.models.artifact import ExecutionArtifact
from app.models.execution_task import ExecutionTask
from app.crud.execution import ExecutionRepository
from app.crud.execution_task import ExecutionTaskRepository
from app.orchestration.state_machine import ExecutionStateMachine
from app.services.audit_service import AuditService
from app.models.execution import Execution
from app.schemas.query import ListQueryParams
from app.utils.time import utcnow
from app.schemas.execution import (
    ExecutionArtifactRead,
    ExecutionCreate,
    ExecutionRead,
    ExecutionTaskRead,
    ExecutionTimelineEntry,
)
from app.services.base import BaseService
from app.services.query_filters import apply_contains_filter, apply_exact_filter, apply_pagination, apply_sort


class ExecutionService(BaseService):
    def __init__(self) -> None:
        self.repo = ExecutionRepository()
        self.task_repo = ExecutionTaskRepository()
        self.audit = AuditService()

    @staticmethod
    def _to_read(execution: Execution) -> ExecutionRead:
        summary = execution.summary_json or {}
        return ExecutionRead(
            id=execution.id,
            project_id=execution.project_id,
            suite_id=execution.suite_id,
            env_id=execution.env_id,
            trigger_type=execution.trigger_type,
            trigger_source=execution.trigger_source,
            request_params=execution.request_params_json or {},
            status=execution.status,
            summary=summary,
            completion_source=summary.get("completion_source"),
            started_at=summary.get("started_at"),
            completed_at=summary.get("completed_at"),
        )

    def list_executions(self, db: Session, *, query: ListQueryParams) -> list[ExecutionRead]:
        statement = select(Execution)
        statement = apply_exact_filter(statement, Execution.status, query.status)
        statement = apply_exact_filter(statement, Execution.project_id, query.project_id)
        statement = apply_exact_filter(statement, Execution.suite_id, query.suite_id)
        statement = apply_contains_filter(
            statement,
            [Execution.id, Execution.trigger_type, Execution.trigger_source, Execution.error_message],
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
                "trigger_type": Execution.trigger_type,
            },
            default="-id",
        )
        statement = apply_pagination(statement, page=query.page, page_size=query.page_size)
        return [self._to_read(execution) for execution in db.scalars(statement).all()]

    def get_execution(self, db: Session, execution_id: str) -> ExecutionRead:
        return self._to_read(self.repo.get(db, execution_id))

    def update_status(
        self,
        db: Session,
        execution_id: str,
        *,
        status: str,
        summary: dict | None = None,
        error_message: str | None = None,
    ) -> ExecutionRead:
        execution = self.repo.get(db, execution_id)
        state_machine = ExecutionStateMachine(execution.status or "created")
        state_machine.transition(status)
        execution.status = state_machine.state
        if summary is not None:
            if status in {"success", "failed", "timeout"}:
                summary = dict(summary)
                summary.setdefault("completed_at", utcnow().isoformat())
            execution.summary_json = summary
        if error_message is not None:
            execution.error_message = error_message
        db.commit()
        db.refresh(execution)
        return self._to_read(execution)

    def mark_queued(self, db: Session, execution_id: str) -> ExecutionRead:
        return self.update_status(db, execution_id, status="queued")

    def mark_running(self, db: Session, execution_id: str) -> ExecutionRead:
        return self.update_status(db, execution_id, status="running")

    def mark_terminal(self, db: Session, execution_id: str, *, status: str, summary: dict) -> ExecutionRead:
        if status not in {"success", "failed"}:
            raise ValueError(f"unsupported terminal status: {status}")
        return self.update_status(db, execution_id, status=status, summary=summary)

    def mark_completed(self, db: Session, execution_id: str, *, status: str, summary: dict) -> ExecutionRead:
        return self.mark_terminal(db, execution_id, status=status, summary=summary)

    def mark_timeout(self, db: Session, execution_id: str, *, summary: dict) -> ExecutionRead:
        return self.update_status(db, execution_id, status="timeout", summary=summary)

    def update_summary(self, db: Session, execution_id: str, summary: dict) -> ExecutionRead:
        execution = self.repo.get(db, execution_id)
        execution.summary_json = summary
        db.commit()
        db.refresh(execution)
        return self._to_read(execution)

    def list_artifacts(self, db: Session, execution_id: str) -> list[ExecutionArtifactRead]:
        self.repo.get(db, execution_id)
        statement = select(ExecutionArtifact).where(ExecutionArtifact.execution_id == execution_id)
        return [
            ExecutionArtifactRead(
                id=artifact.id,
                execution_id=artifact.execution_id,
                artifact_type=artifact.artifact_type,
                name=artifact.name,
                storage_uri=artifact.storage_uri,
            )
            for artifact in db.scalars(statement).all()
        ]

    def list_tasks(self, db: Session, execution_id: str) -> list[ExecutionTaskRead]:
        self.repo.get(db, execution_id)
        order_value = case((ExecutionTask.task_order > 0, ExecutionTask.task_order), else_=9999)
        statement = (
            select(ExecutionTask)
            .where(ExecutionTask.execution_id == execution_id)
            .order_by(order_value, ExecutionTask.task_key, ExecutionTask.id)
        )
        return [
            ExecutionTaskRead(
                id=task.id,
                execution_id=task.execution_id,
                task_key=task.task_key,
                task_name=task.task_name,
                status=task.status,
                input=task.input_json or {},
                output=task.output_json or {},
                error_message=task.error_message,
            )
            for task in db.scalars(statement).all()
        ]

    def create_task(
        self,
        db: Session,
        *,
        execution_id: str,
        task_key: str,
        task_name: str,
        task_order: int,
        input_json: dict | None = None,
    ) -> ExecutionTaskRead:
        task = ExecutionTask(
            id=f"task_{uuid4().hex[:12]}",
            execution_id=execution_id,
            task_key=task_key,
            task_name=task_name,
            task_order=task_order,
            status="running",
            input_json=input_json or {},
            output_json={},
        )
        self.task_repo.add(db, task)
        return ExecutionTaskRead(
            id=task.id,
            execution_id=task.execution_id,
            task_key=task.task_key,
            task_name=task.task_name,
            status=task.status,
            input=task.input_json or {},
            output=task.output_json or {},
            error_message=task.error_message,
        )

    def update_task_status(
        self,
        db: Session,
        task_id: str,
        *,
        status: str,
        output_json: dict | None = None,
        error_message: str | None = None,
    ) -> ExecutionTaskRead:
        task = self.task_repo.get(db, task_id)
        task.status = status
        if output_json is not None:
            task.output_json = output_json
        if error_message is not None:
            task.error_message = error_message
        db.commit()
        db.refresh(task)
        return ExecutionTaskRead(
            id=task.id,
            execution_id=task.execution_id,
            task_key=task.task_key,
            task_name=task.task_name,
            status=task.status,
            input=task.input_json or {},
            output=task.output_json or {},
            error_message=task.error_message,
        )

    def record_artifact(
        self,
        db: Session,
        *,
        execution_id: str,
        artifact_type: str,
        name: str,
        storage_uri: str,
    ) -> ExecutionArtifactRead:
        artifact = ExecutionArtifact(
            id=f"art_{uuid4().hex[:12]}",
            execution_id=execution_id,
            artifact_type=artifact_type,
            name=name,
            storage_uri=storage_uri,
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return ExecutionArtifactRead(
            id=artifact.id,
            execution_id=artifact.execution_id,
            artifact_type=artifact.artifact_type,
            name=artifact.name,
            storage_uri=artifact.storage_uri,
        )

    def get_timeline(self, db: Session, execution_id: str) -> list[ExecutionTimelineEntry]:
        execution = self.repo.get(db, execution_id)
        status_label = execution.status or "created"
        summary = execution.summary_json or {}
        tasks = self.list_tasks(db, execution_id)
        task_entries = [
            ExecutionTimelineEntry(
                stage=task.task_key,
                status=task.status,
                message=task.task_name if task.status != "failed" else f"{task.task_name} failed",
            )
            for task in tasks
        ]
        return [
            ExecutionTimelineEntry(stage="created", status="done", message=f"Execution {execution.id} created"),
            ExecutionTimelineEntry(stage="queued", status="done" if status_label != "created" else "current", message="Execution queued"),
            ExecutionTimelineEntry(stage="running", status="done" if status_label in {"running", "success", "failed"} else "pending", message="Execution running"),
            *task_entries,
            ExecutionTimelineEntry(
                stage="completed",
                status=status_label,
                message=(
                    f"Finished with {summary.get('passed', 0)} passed / {summary.get('failed', 0)} failed"
                    if status_label in {"success", "failed"}
                    else "Awaiting completion"
                ),
            ),
        ]

    def create_execution(self, db: Session, payload: ExecutionCreate) -> ExecutionRead:
        execution = Execution(
            id=f"exe_{uuid4().hex[:12]}",
            project_id=payload.project_id,
            suite_id=payload.suite_id,
            env_id=payload.env_id,
            trigger_type=payload.trigger_type,
            trigger_source=payload.trigger_source,
            request_params_json=payload.request_params,
            status="queued",
            summary_json={},
        )
        self.repo.add(db, execution)
        self.audit.record(
            db,
            actor_id="user_demo",
            action="create_execution",
            target_type="execution",
            target_id=execution.id,
            request_json=payload.model_dump(),
            response_json=self._to_read(execution).model_dump(),
        )
        return ExecutionRead(
            id=execution.id,
            project_id=execution.project_id,
            suite_id=execution.suite_id,
            env_id=execution.env_id,
            trigger_type=execution.trigger_type,
            trigger_source=execution.trigger_source,
            request_params=execution.request_params_json or {},
            status=execution.status,
            summary=execution.summary_json or {},
        )
