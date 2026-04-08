from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError

ModelT = TypeVar("ModelT")


class Repository(Generic[ModelT]):
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    def list(self, db: Session) -> list[ModelT]:
        statement = select(self.model)
        return list(db.scalars(statement).all())

    def get(self, db: Session, object_id: str) -> ModelT:
        obj = db.get(self.model, object_id)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} {object_id} not found")
        return obj

    def add(self, db: Session, obj: ModelT) -> ModelT:
        try:
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj
        except Exception:
            db.rollback()
            raise

    def delete(self, db: Session, obj: ModelT) -> None:
        try:
            db.delete(obj)
            db.commit()
        except Exception:
            db.rollback()
            raise
