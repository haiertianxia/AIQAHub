from pydantic import BaseModel


class SettingsRead(BaseModel):
    environment: str
    revision_number: int
    app_name: str
    app_version: str
    log_level: str
    database_url: str
    redis_url: str
    jenkins_url: str
    jenkins_user: str
    ai_provider: str = "mock"
    ai_model_name: str = "mock-llm"


class SettingsUpdate(BaseModel):
    app_name: str | None = None
    app_version: str | None = None
    log_level: str | None = None
    jenkins_url: str | None = None
    jenkins_user: str | None = None
    ai_provider: str | None = None
    ai_model_name: str | None = None


class SettingsRollback(BaseModel):
    environment: str
    revision_number: int


class SettingsHistoryEntry(BaseModel):
    environment: str
    revision_number: int
    action: str
    app_name: str
    app_version: str
    log_level: str
    jenkins_url: str
    jenkins_user: str
    ai_provider: str = "mock"
    ai_model_name: str = "mock-llm"
    updated_at: str

    def governance_source_id(self) -> str:
        return f"{self.environment}:{self.revision_number}"
