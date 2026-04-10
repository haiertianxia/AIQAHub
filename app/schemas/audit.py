from pydantic import BaseModel, Field

from app.schemas.asset import AssetRevisionRead
from app.schemas.connector import ConnectorRead
from app.schemas.settings import SettingsHistoryEntry


class AuditLogRead(BaseModel):
    id: str
    actor_id: str | None = None
    action: str
    target_type: str
    target_id: str
    request_json: dict = Field(default_factory=dict)
    response_json: dict = Field(default_factory=dict)

    def governance_summary(self) -> str:
        return f"{self.action} {self.target_type}:{self.target_id}"


class AuditOverviewRead(BaseModel):
    audit_log_count: int
    gate_change_count: int
    settings_revision_count: int
    asset_revision_count: int
    connector_count: int
    connectors: list[ConnectorRead] = Field(default_factory=list)
    recent_audit_logs: list[AuditLogRead] = Field(default_factory=list)
    recent_gate_changes: list[AuditLogRead] = Field(default_factory=list)
    recent_settings_history: list[SettingsHistoryEntry] = Field(default_factory=list)
    recent_asset_revisions: list[AssetRevisionRead] = Field(default_factory=list)
