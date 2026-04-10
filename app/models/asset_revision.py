from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssetRevision(Base):
    __tablename__ = "asset_revisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(64), ForeignKey("assets.id"), index=True)
    revision_number: Mapped[int] = mapped_column(default=1, index=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    asset = relationship("Asset", back_populates="revisions")
