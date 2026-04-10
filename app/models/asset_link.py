from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssetLink(Base):
    __tablename__ = "asset_links"
    __table_args__ = (UniqueConstraint("asset_id", "ref_type", "ref_id", name="uq_asset_links_asset_ref"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(64), ForeignKey("assets.id"), index=True)
    ref_type: Mapped[str] = mapped_column(String(64), index=True)
    ref_id: Mapped[str] = mapped_column(String(64), index=True)
    ref_name: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    asset = relationship("Asset", back_populates="links")
