from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.project import ProjectCreate, ProjectRead
from app.db.session import get_db
from app.services.project_service import ProjectService

router = APIRouter()
service = ProjectService()


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectRead]:
    return service.list_projects(db)


@router.post("", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    return service.create_project(db, payload)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    return service.get_project(db, project_id)
