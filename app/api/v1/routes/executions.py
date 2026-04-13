from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.db.session import get_db
from app.orchestration.engine import OrchestrationEngine
from app.schemas.query import ListQueryParams
from app.schemas.execution import (
    ExecutionArtifactRead,
    ExecutionCreate,
    ExecutionDispatchRead,
    ExecutionRead,
    ExecutionTaskRead,
    ExecutionTimelineEntry,
)
from app.services.execution_service import ExecutionService

router = APIRouter()
service = ExecutionService()


@router.get("", response_model=list[ExecutionRead])
def list_executions(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    suite_id: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> list[ExecutionRead]:
    query = ListQueryParams(
        search=search,
        status=status,
        project_id=project_id,
        suite_id=suite_id,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return service.list_executions(db, query=query)


@router.get("/{execution_id}", response_model=ExecutionRead)
def get_execution(execution_id: str, db: Session = Depends(get_db)) -> ExecutionRead:
    return service.get_execution(db, execution_id)


@router.get("/{execution_id}/artifacts", response_model=list[ExecutionArtifactRead])
def list_execution_artifacts(execution_id: str, db: Session = Depends(get_db)) -> list[ExecutionArtifactRead]:
    return service.list_artifacts(db, execution_id)


@router.get("/{execution_id}/tasks", response_model=list[ExecutionTaskRead])
def list_execution_tasks(execution_id: str, db: Session = Depends(get_db)) -> list[ExecutionTaskRead]:
    return service.list_tasks(db, execution_id)


@router.get("/{execution_id}/timeline", response_model=list[ExecutionTimelineEntry])
def get_execution_timeline(execution_id: str, db: Session = Depends(get_db)) -> list[ExecutionTimelineEntry]:
    return service.get_timeline(db, execution_id)


@router.post("", response_model=ExecutionRead)
def create_execution(payload: ExecutionCreate, db: Session = Depends(get_db)) -> ExecutionRead:
    return service.create_execution(db, payload)


@router.post("/{execution_id}/run", response_model=ExecutionDispatchRead)
def run_execution(execution_id: str, db: Session = Depends(get_db)) -> ExecutionDispatchRead:
    execution = service.get_execution(db, execution_id)
    if execution.status != "queued":
        raise ValidationError("execution must be queued before running")
    return ExecutionDispatchRead(**OrchestrationEngine().queue_execution(execution_id))
