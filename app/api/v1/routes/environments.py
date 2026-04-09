from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.environment import EnvironmentCreate, EnvironmentRead
from app.services.environment_service import EnvironmentService

router = APIRouter()
service = EnvironmentService()


@router.get("", response_model=list[EnvironmentRead])
def list_environments(db: Session = Depends(get_db), project_id: str | None = Query(default=None)) -> list[EnvironmentRead]:
    return service.list_environments(db, project_id=project_id)


@router.get("/{env_id}", response_model=EnvironmentRead)
def get_environment(env_id: str, db: Session = Depends(get_db)) -> EnvironmentRead:
    return service.get_environment(db, env_id)


@router.post("", response_model=EnvironmentRead)
def create_environment(payload: EnvironmentCreate, db: Session = Depends(get_db)) -> EnvironmentRead:
    return service.create_environment(db, payload)
