from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.artifact import ExecutionArtifact
from app.crud.execution import ExecutionRepository
from app.services.audit_service import AuditService
from app.models.execution import Execution
from app.schemas.execution import ExecutionArtifactRead, ExecutionCreate, ExecutionRead, ExecutionTimelineEntry
from app.services.base import BaseService


class ExecutionService(BaseService):
    def __init__(self) -> None:
        self.repo = ExecutionRepository()
        self.audit = AuditService()

    @staticmethod
    def _to_read(execution: Execution) -> ExecutionRead:
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

    def list_executions(self, db: Session) -> list[ExecutionRead]:
        return [self._to_read(execution) for execution in self.repo.list(db)]

    def get_execution(self, db: Session, execution_id: str) -> ExecutionRead:
        return self._to_read(self.repo.get(db, execution_id))

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

    def get_timeline(self, db: Session, execution_id: str) -> list[ExecutionTimelineEntry]:
        execution = self.repo.get(db, execution_id)
        status_label = execution.status or "created"
        summary = execution.summary_json or {}
        return [
            ExecutionTimelineEntry(stage="created", status="done", message=f"Execution {execution.id} created"),
            ExecutionTimelineEntry(stage="queued", status="done" if status_label != "created" else "current", message="Execution queued"),
            ExecutionTimelineEntry(stage="running", status="done" if status_label in {"running", "success", "failed"} else "pending", message="Execution running"),
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
