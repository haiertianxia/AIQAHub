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
    ai_provider: str = "mock"
    ai_model_name: str = "mock-llm"
    notification_default_channel: str = "dingtalk"
    notification_email_enabled: bool = False
    notification_email_smtp_host: str = ""
    notification_email_smtp_port: int = 25
    notification_email_from: str = ""
    notification_email_to: str = ""
    notification_dingtalk_enabled: bool = False
    notification_dingtalk_webhook_url: str = ""
    notification_wecom_enabled: bool = False
    notification_wecom_webhook_url: str = ""
    playwright_enabled: bool = False
    playwright_command: str = ""
    playwright_workdir: str = ""
    playwright_default_base_url: str = ""
    playwright_default_browser: str = "chromium"
    playwright_default_headless: bool = True


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").strip().lower() in {"1", "true", "yes", "on"}


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
        ai_provider=os.getenv("AI_PROVIDER", "mock"),
        ai_model_name=os.getenv("AI_MODEL_NAME", "mock-llm"),
        notification_default_channel=os.getenv("NOTIFICATION_DEFAULT_CHANNEL", "dingtalk"),
        notification_email_enabled=_env_bool("NOTIFICATION_EMAIL_ENABLED", False),
        notification_email_smtp_host=os.getenv("NOTIFICATION_EMAIL_SMTP_HOST", ""),
        notification_email_smtp_port=int(os.getenv("NOTIFICATION_EMAIL_SMTP_PORT", "25")),
        notification_email_from=os.getenv("NOTIFICATION_EMAIL_FROM", ""),
        notification_email_to=os.getenv("NOTIFICATION_EMAIL_TO", ""),
        notification_dingtalk_enabled=_env_bool("NOTIFICATION_DINGTALK_ENABLED", False),
        notification_dingtalk_webhook_url=os.getenv("NOTIFICATION_DINGTALK_WEBHOOK_URL", ""),
        notification_wecom_enabled=_env_bool("NOTIFICATION_WECOM_ENABLED", False),
        notification_wecom_webhook_url=os.getenv("NOTIFICATION_WECOM_WEBHOOK_URL", ""),
        playwright_enabled=_env_bool("PLAYWRIGHT_ENABLED", False),
        playwright_command=os.getenv("PLAYWRIGHT_COMMAND", ""),
        playwright_workdir=os.getenv("PLAYWRIGHT_WORKDIR", ""),
        playwright_default_base_url=os.getenv("PLAYWRIGHT_DEFAULT_BASE_URL", ""),
        playwright_default_browser=os.getenv("PLAYWRIGHT_DEFAULT_BROWSER", "chromium"),
        playwright_default_headless=_env_bool("PLAYWRIGHT_DEFAULT_HEADLESS", True),
    )
