from app.schemas.asset import AssetCreate, AssetRead
from app.services.base import BaseService


class AssetService(BaseService):
    def list_assets(self) -> list[AssetRead]:
        return [AssetRead(id="asset_demo", project_id="proj_demo", asset_type="suite", name="Demo Asset")]

    def create_asset(self, payload: AssetCreate) -> AssetRead:
        return AssetRead(
            id="asset_demo",
            project_id=payload.project_id,
            asset_type=payload.asset_type,
            name=payload.name,
            version=payload.version,
            source_ref=payload.source_ref,
            metadata=payload.metadata,
        )

