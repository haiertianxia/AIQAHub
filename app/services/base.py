from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError


class BaseService:
    """Shared service skeleton."""

    @staticmethod
    def _commit(db: Session) -> None:
        db.commit()

    @staticmethod
    def _refresh(db: Session, obj) -> None:
        db.refresh(obj)

