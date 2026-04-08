from pydantic import BaseModel


class SettingsRead(BaseModel):
    app_name: str
    app_version: str
    log_level: str
    database_url: str
    redis_url: str
