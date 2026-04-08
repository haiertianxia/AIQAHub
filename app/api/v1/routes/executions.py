from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.execution import ExecutionArtifactRead, ExecutionCreate, ExecutionRead, ExecutionTimelineEntry
from app.services.execution_service import ExecutionService

router = APIRouter()
service = ExecutionService()


@router.get("", response_model=list[ExecutionRead])
def list_executions(db: Session = Depends(get_db)) -> list[ExecutionRead]:
    return service.list_executions(db)


@router.get("/{execution_id}", response_model=ExecutionRead)
def get_execution(execution_id: str, db: Session = Depends(get_db)) -> ExecutionRead:
    return service.get_execution(db, execution_id)


@router.get("/{execution_id}/artifacts", response_model=list[ExecutionArtifactRead])
def list_execution_artifacts(execution_id: str, db: Session = Depends(get_db)) -> list[ExecutionArtifactRead]:
    return service.list_artifacts(db, execution_id)


@router.get("/{execution_id}/timeline", response_model=list[ExecutionTimelineEntry])
def get_execution_timeline(execution_id: str, db: Session = Depends(get_db)) -> list[ExecutionTimelineEntry]:
    return service.get_timeline(db, execution_id)


@router.post("", response_model=ExecutionRead)
def create_execution(payload: ExecutionCreate, db: Session = Depends(get_db)) -> ExecutionRead:
    return service.create_execution(db, payload)
