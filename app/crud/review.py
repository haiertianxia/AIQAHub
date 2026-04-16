from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import Repository
from app.models.review import (
    ReviewTask,
    ReviewComment,
    ReviewChecklist,
    ReviewScore,
)


class ReviewTaskRepository(Repository[ReviewTask]):
    def __init__(self) -> None:
        super().__init__(ReviewTask)

    def list_by_document(self, db: Session, document_id: str) -> list[ReviewTask]:
        statement = select(ReviewTask).where(ReviewTask.document_id == document_id)
        return list(db.scalars(statement).all())

    def list_by_project(self, db: Session, project_id: str) -> list[ReviewTask]:
        statement = select(ReviewTask).where(ReviewTask.project_id == project_id)
        return list(db.scalars(statement).all())

    def list_by_status(self, db: Session, project_id: str, status: str) -> list[ReviewTask]:
        statement = select(ReviewTask).where(
            ReviewTask.project_id == project_id,
            ReviewTask.status == status
        )
        return list(db.scalars(statement).all())


class ReviewCommentRepository(Repository[ReviewComment]):
    def __init__(self) -> None:
        super().__init__(ReviewComment)

    def list_by_review_task(self, db: Session, review_task_id: str) -> list[ReviewComment]:
        statement = select(ReviewComment).where(
            ReviewComment.review_task_id == review_task_id
        )
        return list(db.scalars(statement).all())

    def list_by_document(self, db: Session, document_id: str) -> list[ReviewComment]:
        statement = select(ReviewComment).where(ReviewComment.document_id == document_id)
        return list(db.scalars(statement).all())


class ReviewChecklistRepository(Repository[ReviewChecklist]):
    def __init__(self) -> None:
        super().__init__(ReviewChecklist)

    def list_by_review_task(self, db: Session, review_task_id: str) -> list[ReviewChecklist]:
        statement = select(ReviewChecklist).where(
            ReviewChecklist.review_task_id == review_task_id
        ).order_by(ReviewChecklist.sort_order)
        return list(db.scalars(statement).all())


class ReviewScoreRepository(Repository[ReviewScore]):
    def __init__(self) -> None:
        super().__init__(ReviewScore)

    def list_by_review_task(self, db: Session, review_task_id: str) -> list[ReviewScore]:
        statement = select(ReviewScore).where(ReviewScore.review_task_id == review_task_id)
        return list(db.scalars(statement).all())

    def list_by_document(self, db: Session, document_id: str) -> list[ReviewScore]:
        statement = select(ReviewScore).where(ReviewScore.document_id == document_id)
        return list(db.scalars(statement).all())
