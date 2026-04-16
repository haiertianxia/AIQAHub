from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import Repository
from app.models.document import Document, DocumentVersion


class DocumentRepository(Repository[Document]):
    def __init__(self) -> None:
        super().__init__(Document)

    def list_by_project(self, db: Session, project_id: str) -> list[Document]:
        statement = select(Document).where(Document.project_id == project_id)
        return list(db.scalars(statement).all())

    def list_by_type(self, db: Session, project_id: str, doc_type: str) -> list[Document]:
        statement = select(Document).where(
            Document.project_id == project_id,
            Document.doc_type == doc_type
        )
        return list(db.scalars(statement).all())


class DocumentVersionRepository(Repository[DocumentVersion]):
    def __init__(self) -> None:
        super().__init__(DocumentVersion)

    def list_by_document(self, db: Session, document_id: str) -> list[DocumentVersion]:
        statement = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version.desc())
        return list(db.scalars(statement).all())

    def get_latest(self, db: Session, document_id: str) -> DocumentVersion | None:
        statement = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version.desc()).limit(1)
        return db.scalars(statement).first()

    def get_by_version(self, db: Session, document_id: str, version: int) -> DocumentVersion | None:
        statement = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version == version
        )
        return db.scalars(statement).first()
