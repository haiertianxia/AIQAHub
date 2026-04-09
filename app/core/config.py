from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(slots=True)
class Settings:
    app_name: str = "AIQAHub"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./aiqahub.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    jenkins_url: str = ""
    jenkins_user: str = ""
    jenkins_token: str = ""
    jenkins_webhook_secret: str = "change-me-webhook"
    jenkins_webhook_tolerance_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AIQAHub"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./aiqahub.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        secret_key=os.getenv("SECRET_KEY", "change-me"),
        jenkins_url=os.getenv("JENKINS_URL", ""),
        jenkins_user=os.getenv("JENKINS_USER", ""),
        jenkins_token=os.getenv("JENKINS_TOKEN", ""),
        jenkins_webhook_secret=os.getenv("JENKINS_WEBHOOK_SECRET", "change-me-webhook"),
        jenkins_webhook_tolerance_seconds=int(os.getenv("JENKINS_WEBHOOK_TOLERANCE_SECONDS", "300")),
    )
