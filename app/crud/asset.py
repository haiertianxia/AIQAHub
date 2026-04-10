from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.base import Repository
from app.models.asset import Asset
from app.models.asset_link import AssetLink
from app.models.asset_revision import AssetRevision


class AssetRepository(Repository[Asset]):
    def __init__(self) -> None:
        super().__init__(Asset)

    def list_revisions(self, db: Session, asset_id: str) -> list[AssetRevision]:
        statement = select(AssetRevision).where(AssetRevision.asset_id == asset_id).order_by(
            AssetRevision.revision_number.asc(), AssetRevision.created_at.asc()
        )
        return list(db.scalars(statement).all())

    def next_revision_number(self, db: Session, asset_id: str) -> int:
        statement = select(func.coalesce(func.max(AssetRevision.revision_number), 0)).where(
            AssetRevision.asset_id == asset_id
        )
        return int(db.scalar(statement) or 0) + 1

    def list_links(self, db: Session, asset_id: str) -> list[AssetLink]:
        statement = select(AssetLink).where(AssetLink.asset_id == asset_id).order_by(AssetLink.created_at.asc())
        return list(db.scalars(statement).all())

    def has_links(self, db: Session, asset_id: str) -> bool:
        statement = select(func.count()).select_from(AssetLink).where(AssetLink.asset_id == asset_id)
        return int(db.scalar(statement) or 0) > 0

    def get_link_by_identity(self, db: Session, asset_id: str, ref_type: str, ref_id: str) -> AssetLink | None:
        statement = (
            select(AssetLink)
            .where(AssetLink.asset_id == asset_id)
            .where(AssetLink.ref_type == ref_type)
            .where(AssetLink.ref_id == ref_id)
        )
        return db.scalars(statement).one_or_none()
