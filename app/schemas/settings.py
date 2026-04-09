from pydantic import BaseModel


class SettingsRead(BaseModel):
    app_name: str
    app_version: str
    log_level: str
    database_url: str
    redis_url: str
    jenkins_url: str
    jenkins_user: str


class SettingsUpdate(BaseModel):
    app_name: str | None = None
    app_version: str | None = None
    log_level: str | None = None
    jenkins_url: str | None = None
    jenkins_user: str | None = None
