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

