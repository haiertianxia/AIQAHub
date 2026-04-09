from uuid import uuid4

from sqlalchemy.orm import Session

from app.crud.asset import AssetRepository
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetRead
from app.services.base import BaseService


class AssetService(BaseService):
    def __init__(self) -> None:
        self.repo = AssetRepository()

    @staticmethod
    def _to_read(asset: Asset) -> AssetRead:
        return AssetRead(
            id=asset.id,
            project_id=asset.project_id,
            asset_type=asset.asset_type,
            name=asset.name,
            version=asset.version,
            source_ref=asset.source_ref,
            metadata=asset.metadata_json or {},
            status=asset.status,
        )

    def list_assets(self, db: Session) -> list[AssetRead]:
        return [self._to_read(asset) for asset in self.repo.list(db)]

    def create_asset(self, db: Session, payload: AssetCreate) -> AssetRead:
        asset = Asset(
            id=f"asset_{uuid4().hex[:12]}",
            project_id=payload.project_id,
            asset_type=payload.asset_type,
            name=payload.name,
            version=payload.version,
            source_ref=payload.source_ref,
            metadata_json=payload.metadata,
        )
        created = self.repo.add(db, asset)
        return self._to_read(created)
