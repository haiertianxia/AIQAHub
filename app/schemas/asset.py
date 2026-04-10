from datetime import datetime

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    project_id: str
    asset_type: str
    name: str
    version: str | None = None
    source_ref: str | None = None
    metadata: dict = Field(default_factory=dict)


class AssetRead(AssetCreate):
    id: str
    status: str = "active"


class AssetRevisionRead(BaseModel):
    id: str
    asset_id: str
    revision_number: int
    version: str | None = None
    snapshot: dict = Field(default_factory=dict)
    change_summary: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None

    def governance_source_id(self) -> str:
        return self.id


class AssetLinkCreate(BaseModel):
    ref_type: str
    ref_id: str
    ref_name: str
    reason: str


class AssetLinkRead(AssetLinkCreate):
    id: str
    asset_id: str
    created_at: datetime | None = None

    def governance_source_id(self) -> str:
        return self.id


class AssetImpactRead(BaseModel):
    asset: AssetRead
    reference_count: int = 0
    reference_summary: dict[str, int] = Field(default_factory=dict)
    references: list[AssetLinkRead] = Field(default_factory=list)
    can_archive: bool = True
    blocking_reasons: list[str] = Field(default_factory=list)
