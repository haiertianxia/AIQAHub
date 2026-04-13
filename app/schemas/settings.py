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


class SettingsUpdate(BaseModel):
    app_name: str | None = None
    app_version: str | None = None
    log_level: str | None = None
    jenkins_url: str | None = None
    jenkins_user: str | None = None
    ai_provider: str | None = None
    ai_model_name: str | None = None
    notification_default_channel: str | None = None
    notification_email_enabled: bool | None = None
    notification_email_smtp_host: str | None = None
    notification_email_smtp_port: int | None = None
    notification_email_from: str | None = None
    notification_email_to: str | None = None
    notification_dingtalk_enabled: bool | None = None
    notification_dingtalk_webhook_url: str | None = None
    notification_wecom_enabled: bool | None = None
    notification_wecom_webhook_url: str | None = None


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
    updated_at: str

    def governance_source_id(self) -> str:
        return f"{self.environment}:{self.revision_number}"
