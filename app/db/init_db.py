from app.db.base import Base
from app.db.seed import seed_demo_data
from app import models  # noqa: F401  # ensure model registration
from app.db.session import SessionLocal, engine


def create_all_tables() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)
