from uuid import uuid4

from sqlalchemy.orm import Session

from app.crud.project import ProjectRepository
from app.services.audit_service import AuditService
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.base import BaseService


class ProjectService(BaseService):
    def __init__(self) -> None:
        self.repo = ProjectRepository()
        self.audit = AuditService()

    @staticmethod
    def _to_read(project: Project) -> ProjectRead:
        return ProjectRead(
            id=project.id,
            code=project.code,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            status=project.status,
        )

    def list_projects(self, db: Session) -> list[ProjectRead]:
        return [self._to_read(project) for project in self.repo.list(db)]

    def create_project(self, db: Session, payload: ProjectCreate) -> ProjectRead:
        project = Project(
            id=f"proj_{uuid4().hex[:12]}",
            code=payload.code,
            name=payload.name,
            description=payload.description,
        )
        created = self.repo.add(db, project)
        self.audit.record(
            db,
            actor_id="user_demo",
            action="create_project",
            target_type="project",
            target_id=created.id,
            request_json=payload.model_dump(),
            response_json=self._to_read(created).model_dump(),
        )
        return self._to_read(created)

    def get_project(self, db: Session, project_id: str) -> ProjectRead:
        return self._to_read(self.repo.get(db, project_id))
