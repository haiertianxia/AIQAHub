from pydantic import BaseModel, Field


class TestSuiteBase(BaseModel):
    project_id: str
    name: str
    suite_type: str
    source_type: str
    source_ref: str


class TestSuiteCreate(TestSuiteBase):
    default_env_id: str | None = None


class TestSuiteRead(TestSuiteBase):
    id: str
    default_env_id: str | None = None
    status: str = "enabled"

