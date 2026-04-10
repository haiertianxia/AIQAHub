from uuid import uuid4

from sqlalchemy.orm import Session

from app.crud.asset import AssetRepository
from app.models.asset import Asset
from app.models.asset_revision import AssetRevision
from app.schemas.asset import AssetCreate, AssetRead, AssetRevisionRead
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

    @staticmethod
    def _to_revision_read(revision: AssetRevision) -> AssetRevisionRead:
        return AssetRevisionRead(
            id=revision.id,
            asset_id=revision.asset_id,
            revision_number=revision.revision_number,
            version=revision.version,
            snapshot=revision.snapshot_json,
            change_summary=revision.change_summary,
            created_by=revision.created_by,
            created_at=revision.created_at,
        )

    @staticmethod
    def _asset_snapshot(asset: Asset) -> dict:
        return AssetRead(
            id=asset.id,
            project_id=asset.project_id,
            asset_type=asset.asset_type,
            name=asset.name,
            version=asset.version,
            source_ref=asset.source_ref,
            metadata=asset.metadata_json or {},
            status=asset.status,
        ).model_dump()

    def _write_revision(self, db: Session, asset: Asset, *, change_summary: str | None = None) -> None:
        revision = AssetRevision(
            id=f"assetrev_{uuid4().hex[:12]}",
            asset_id=asset.id,
            revision_number=self.repo.next_revision_number(db, asset.id),
            version=asset.version,
            snapshot_json=self._asset_snapshot(asset),
            change_summary=change_summary,
        )
        db.add(revision)

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
        try:
            db.add(asset)
            db.flush()
            self._write_revision(db, asset, change_summary="created")
            db.commit()
            db.refresh(asset)
            return self._to_read(asset)
        except Exception:
            db.rollback()
            raise

    def update_asset(self, db: Session, asset_id: str, payload: AssetCreate) -> AssetRead:
        asset = self.repo.get(db, asset_id)
        try:
            asset.project_id = payload.project_id
            asset.asset_type = payload.asset_type
            asset.name = payload.name
            asset.version = payload.version
            asset.source_ref = payload.source_ref
            asset.metadata_json = payload.metadata
            self._write_revision(db, asset, change_summary="updated")
            db.commit()
            db.refresh(asset)
            return self._to_read(asset)
        except Exception:
            db.rollback()
            raise

    def list_asset_revisions(self, db: Session, asset_id: str) -> list[AssetRevisionRead]:
        self.repo.get(db, asset_id)
        return [self._to_revision_read(revision) for revision in self.repo.list_revisions(db, asset_id)]
