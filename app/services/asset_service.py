from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.asset import AssetRepository
from app.models.asset import Asset
from app.models.asset_link import AssetLink
from app.models.asset_revision import AssetRevision
from app.core.exceptions import ValidationError
from app.schemas.asset import (
    AssetCreate,
    AssetImpactRead,
    AssetLinkCreate,
    AssetLinkRead,
    AssetRead,
    AssetRevisionRead,
)
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
    def _to_link_read(link: AssetLink) -> AssetLinkRead:
        return AssetLinkRead(
            id=link.id,
            asset_id=link.asset_id,
            ref_type=link.ref_type,
            ref_id=link.ref_id,
            ref_name=link.ref_name,
            reason=link.reason,
            created_at=link.created_at,
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

    def list_asset_links(self, db: Session, asset_id: str) -> list[AssetLinkRead]:
        self.repo.get(db, asset_id)
        return [self._to_link_read(link) for link in self.repo.list_links(db, asset_id)]

    def get_asset_impact(self, db: Session, asset_id: str) -> AssetImpactRead:
        asset = self.repo.get(db, asset_id)
        links = self.repo.list_links(db, asset_id)
        reference_summary: dict[str, int] = {}
        for link in links:
            reference_summary[link.ref_type] = reference_summary.get(link.ref_type, 0) + 1
        blocking_reasons = []
        if links:
            blocking_reasons.append("active references exist")
        return AssetImpactRead(
            asset=self._to_read(asset),
            reference_count=len(links),
            reference_summary=reference_summary,
            references=[self._to_link_read(link) for link in links],
            can_archive=not links,
            blocking_reasons=blocking_reasons,
        )

    def create_asset_link(self, db: Session, asset_id: str, payload: AssetLinkCreate) -> AssetLinkRead:
        asset = self.repo.get(db, asset_id)
        if self.repo.get_link_by_identity(db, asset.id, payload.ref_type, payload.ref_id) is not None:
            raise ValidationError("duplicate asset link")
        link = AssetLink(
            id=f"assetlink_{uuid4().hex[:12]}",
            asset_id=asset.id,
            ref_type=payload.ref_type,
            ref_id=payload.ref_id,
            ref_name=payload.ref_name,
            reason=payload.reason,
        )
        try:
            db.add(link)
            db.commit()
            db.refresh(link)
            return self._to_link_read(link)
        except Exception:
            db.rollback()
            raise

    def delete_asset_link(self, db: Session, asset_id: str, link_id: str) -> None:
        asset = self.repo.get(db, asset_id)
        statement = select(AssetLink).where(AssetLink.id == link_id).where(AssetLink.asset_id == asset.id)
        link = db.scalars(statement).one_or_none()
        if link is None:
            raise ValidationError("asset link not found")
        try:
            db.delete(link)
            db.commit()
        except Exception:
            db.rollback()
            raise

    def delete_asset(self, db: Session, asset_id: str) -> AssetRead:
        asset = self.repo.get(db, asset_id)
        if self.repo.has_links(db, asset.id):
            raise ValidationError("asset has active references")
        try:
            asset.status = "archived"
            self._write_revision(db, asset, change_summary="archived")
            db.commit()
            db.refresh(asset)
            return self._to_read(asset)
        except Exception:
            db.rollback()
            raise
