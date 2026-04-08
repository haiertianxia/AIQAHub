from pydantic import BaseModel


class EnvironmentBase(BaseModel):
    project_id: str
    name: str
    env_type: str
    base_url: str


class EnvironmentCreate(EnvironmentBase):
    credential_ref: str | None = None
    db_ref: str | None = None


class EnvironmentRead(EnvironmentBase):
    id: str
    credential_ref: str | None = None
    db_ref: str | None = None
    enabled: bool = True

