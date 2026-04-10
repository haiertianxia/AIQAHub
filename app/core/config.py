from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(slots=True)
class Settings:
    app_name: str = "AIQAHub"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    app_env: str = "local"
    database_url: str = "sqlite:///./aiqahub.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    jenkins_url: str = ""
    jenkins_user: str = ""
    jenkins_token: str = ""
    jenkins_webhook_secret: str = "change-me-webhook"
    jenkins_webhook_tolerance_seconds: int = 300
    execution_timeout_seconds: int = 3600
    jenkins_poll_attempts: int = 3
    jenkins_poll_delay_seconds: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AIQAHub"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        app_env=os.getenv("APP_ENV", "local"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./aiqahub.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        secret_key=os.getenv("SECRET_KEY", "change-me"),
        jenkins_url=os.getenv("JENKINS_URL", ""),
        jenkins_user=os.getenv("JENKINS_USER", ""),
        jenkins_token=os.getenv("JENKINS_TOKEN", ""),
        jenkins_webhook_secret=os.getenv("JENKINS_WEBHOOK_SECRET", "change-me-webhook"),
        jenkins_webhook_tolerance_seconds=int(os.getenv("JENKINS_WEBHOOK_TOLERANCE_SECONDS", "300")),
        execution_timeout_seconds=int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "3600")),
        jenkins_poll_attempts=int(os.getenv("JENKINS_POLL_ATTEMPTS", "3")),
        jenkins_poll_delay_seconds=int(os.getenv("JENKINS_POLL_DELAY_SECONDS", "5")),
    )
