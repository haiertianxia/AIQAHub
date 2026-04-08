from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: str
    owner_id: str | None = None
    status: str = "active"

