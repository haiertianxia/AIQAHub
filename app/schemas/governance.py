from datetime import UTC, datetime
from hashlib import sha1
from typing import Literal

from pydantic import BaseModel, Field


GovernanceEventKind = Literal[
    "asset_change",
    "asset_block",
    "gate_change",
    "gate_fail",
    "settings_update",
    "settings_rollback",
    "connector_status",
    "audit_event",
]
GovernanceSeverity = Literal["info", "warn", "error", "blocked"]


def stable_governance_event_id(kind: GovernanceEventKind, source_type: str, source_id: str) -> str:
    key = f"{kind}|{source_type}|{source_id}"
    return f"gov_{sha1(key.encode('utf-8')).hexdigest()[:16]}"


def normalize_utc_timestamp(value: datetime | str | None) -> str:
    if isinstance(value, str):
        candidate = value.strip()
        if candidate:
            try:
                parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
            except ValueError:
                parsed = datetime(1970, 1, 1, tzinfo=UTC)
            else:
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, datetime):
        parsed = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return datetime(1970, 1, 1, tzinfo=UTC).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: datetime | str | None) -> datetime:
    normalized = normalize_utc_timestamp(value)
    return datetime.fromisoformat(normalized.replace("Z", "+00:00"))


class GovernanceEventRead(BaseModel):
    id: str
    kind: GovernanceEventKind
    source_type: str
    source_id: str
    timestamp: str
    severity: GovernanceSeverity = "info"
    status: str | None = None
    project_id: str | None = None
    environment: str | None = None
    title: str
    description: str | None = None
    metadata: dict = Field(default_factory=dict)


class GovernanceEventDetailRead(GovernanceEventRead):
    raw: dict = Field(default_factory=dict)


class GovernanceOverviewRead(BaseModel):
    window: str = "last_24h"
    window_start: str
    window_end: str
    asset_block_count: int = 0
    gate_fail_count: int = 0
    settings_rollback_count: int = 0
    connector_error_count: int = 0
    recent_audit_count: int = 0
    recent_events: list[GovernanceEventRead] = Field(default_factory=list)
