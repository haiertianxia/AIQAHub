from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentRead,
    DocumentVersionRead,
    ReviewTaskCreate,
    ReviewTaskUpdate,
    ReviewTaskRead,
    ReviewCommentCreate,
    ReviewCommentUpdate,
    ReviewCommentRead,
    ReviewChecklistCreate,
    ReviewChecklistUpdate,
    ReviewChecklistRead,
    ReviewScoreCreate,
    ReviewScoreRead,
)
from app.services.document_service import DocumentService, ReviewService

router = APIRouter(prefix="/documents", tags=["documents"])
doc_service = DocumentService()
review_service = ReviewService()


# Document endpoints
@router.get("", response_model=list[DocumentRead])
def list_documents(
    project_id: str = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return doc_service.list_documents(db, project_id)


@router.get("/{doc_id}", response_model=DocumentRead)
def get_document(doc_id: str, db: Session = Depends(get_db)) -> DocumentRead:
    return doc_service.get_document(db, doc_id)


@router.post("", response_model=DocumentRead)
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)) -> DocumentRead:
    return doc_service.create_document(db, payload)


@router.put("/{doc_id}", response_model=DocumentRead)
def update_document(doc_id: str, payload: DocumentUpdate, db: Session = Depends(get_db)) -> DocumentRead:
    return doc_service.update_document(db, doc_id, payload)


@router.get("/{doc_id}/versions", response_model=list[DocumentVersionRead])
def list_document_versions(doc_id: str, db: Session = Depends(get_db)) -> list[DocumentVersionRead]:
    return doc_service.list_versions(db, doc_id)


# Review Task endpoints
@router.post("/{doc_id}/review-tasks", response_model=ReviewTaskRead)
def create_review_task(
    doc_id: str,
    payload: ReviewTaskCreate,
    db: Session = Depends(get_db),
) -> ReviewTaskRead:
    return review_service.create_review_task(db, payload)


@router.put("/review-tasks/{task_id}", response_model=ReviewTaskRead)
def update_review_task(
    task_id: str,
    payload: ReviewTaskUpdate,
    db: Session = Depends(get_db),
) -> ReviewTaskRead:
    return review_service.update_review_task(db, task_id, payload)


# Review Comment endpoints
@router.post("/review-tasks/{task_id}/comments", response_model=ReviewCommentRead)
def create_review_comment(
    task_id: str,
    payload: ReviewCommentCreate,
    db: Session = Depends(get_db),
) -> ReviewCommentRead:
    return review_service.create_comment(db, payload)


@router.put("/review-comments/{comment_id}", response_model=ReviewCommentRead)
def update_review_comment(
    comment_id: str,
    payload: ReviewCommentUpdate,
    db: Session = Depends(get_db),
) -> ReviewCommentRead:
    return review_service.update_comment(db, comment_id, payload)


# Review Checklist endpoints
@router.post("/review-tasks/{task_id}/checklist", response_model=ReviewChecklistRead)
def create_checklist_item(
    task_id: str,
    payload: ReviewChecklistCreate,
    db: Session = Depends(get_db),
) -> ReviewChecklistRead:
    return review_service.create_checklist_item(db, payload)


@router.put("/review-checklist/{checklist_id}", response_model=ReviewChecklistRead)
def update_checklist_item(
    checklist_id: str,
    payload: ReviewChecklistUpdate,
    db: Session = Depends(get_db),
) -> ReviewChecklistRead:
    return review_service.update_checklist_item(db, checklist_id, payload)


# Review Score endpoints
@router.post("/review-tasks/{task_id}/scores", response_model=ReviewScoreRead)
def create_review_score(
    task_id: str,
    payload: ReviewScoreCreate,
    db: Session = Depends(get_db),
) -> ReviewScoreRead:
    return review_service.create_score(db, payload)
