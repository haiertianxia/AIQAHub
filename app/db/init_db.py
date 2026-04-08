from sqlalchemy import create_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db.seed import seed_demo_data
from app import models  # noqa: F401  # ensure model registration
from app.db.session import SessionLocal


def create_all_tables() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)
