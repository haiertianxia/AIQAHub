from app.crud.base import Repository
from app.models.project import Project


class ProjectRepository(Repository[Project]):
    def __init__(self) -> None:
        super().__init__(Project)

