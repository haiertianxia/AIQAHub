from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    env_type: Mapped[str] = mapped_column(String(32))
    base_url: Mapped[str] = mapped_column(Text)
    credential_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    db_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

