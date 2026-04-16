from uuid import uuid4
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.document import DocumentRepository, DocumentVersionRepository
from app.crud.review import (
    ReviewTaskRepository,
    ReviewCommentRepository,
    ReviewChecklistRepository,
    ReviewScoreRepository,
)
from app.crud.coverage import CoverageSnapshotRepository, CoverageMetricRepository
from app.models.document import Document, DocumentVersion
from app.models.review import (
    ReviewTask,
    ReviewComment,
    ReviewChecklist,
    ReviewScore,
)
from app.models.coverage import CoverageSnapshot, CoverageMetric
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentRead,
    DocumentVersionCreate,
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
    CoverageSnapshotCreate,
    CoverageSnapshotRead,
    CoverageMetricCreate,
    CoverageMetricRead,
)
from app.services.base import BaseService
from app.services.audit_service import AuditService


class DocumentService(BaseService):
    def __init__(self) -> None:
        self.doc_repo = DocumentRepository()
        self.doc_version_repo = DocumentVersionRepository()
        self.audit = AuditService()

    @staticmethod
    def _to_doc_read(doc: Document) -> DocumentRead:
        return DocumentRead(
            id=doc.id,
            project_id=doc.project_id,
            title=doc.title,
            doc_type=doc.doc_type,
            status=doc.status,
            description=doc.description,
            content=doc.content_json or {},
            metadata=doc.metadata_json or {},
            created_by=doc.created_by,
            updated_by=doc.updated_by,
        )

    @staticmethod
    def _to_doc_version_read(version: DocumentVersion) -> DocumentVersionRead:
        return DocumentVersionRead(
            id=version.id,
            document_id=version.document_id,
            version=version.version,
            title=version.title,
            content=version.content_json or {},
            change_description=version.change_description,
            created_by=version.created_by,
        )

    def list_documents(self, db: Session, project_id: str) -> list[DocumentRead]:
        return [self._to_doc_read(doc) for doc in self.doc_repo.list_by_project(db, project_id)]

    def get_document(self, db: Session, doc_id: str) -> DocumentRead:
        return self._to_doc_read(self.doc_repo.get(db, doc_id))

    def create_document(self, db: Session, payload: DocumentCreate, actor_id: str = "user_demo") -> DocumentRead:
        doc = Document(
            id=f"doc_{uuid4().hex[:12]}",
            project_id=payload.project_id,
            title=payload.title,
            doc_type=payload.doc_type,
            status="draft",
            description=payload.description,
            content_json=payload.content,
            metadata_json=payload.metadata,
            created_by=actor_id,
            updated_by=actor_id,
        )
        created = self.doc_repo.add(db, doc)

        # Create initial version
        self._create_version(db, created, 1, "Initial version", actor_id)

        self.audit.record(
            db,
            actor_id=actor_id,
            action="create_document",
            target_type="document",
            target_id=created.id,
            request_json=payload.model_dump(),
            response_json=self._to_doc_read(created).model_dump(),
        )
        return self._to_doc_read(created)

    def update_document(self, db: Session, doc_id: str, payload: DocumentUpdate, actor_id: str = "user_demo") -> DocumentRead:
        doc = self.doc_repo.get(db, doc_id)

        # Get current latest version
        latest_version = self.doc_version_repo.get_latest(db, doc_id)
        next_version = (latest_version.version if latest_version else 0) + 1

        if payload.title is not None:
            doc.title = payload.title
        if payload.description is not None:
            doc.description = payload.description
        if payload.content is not None:
            doc.content_json = payload.content
        if payload.metadata is not None:
            doc.metadata_json = payload.metadata
        if payload.status is not None:
            doc.status = payload.status

        doc.updated_by = actor_id
        db.commit()
        db.refresh(doc)

        # Create new version
        self._create_version(db, doc, next_version, "Updated", actor_id)

        self.audit.record(
            db,
            actor_id=actor_id,
            action="update_document",
            target_type="document",
            target_id=doc.id,
            request_json=payload.model_dump(exclude_none=True),
            response_json=self._to_doc_read(doc).model_dump(),
        )
        return self._to_doc_read(doc)

    def _create_version(self, db: Session, doc: Document, version: int, change_desc: str, actor_id: str) -> DocumentVersion:
        doc_version = DocumentVersion(
            id=f"docver_{uuid4().hex[:12]}",
            document_id=doc.id,
            version=version,
            title=doc.title,
            content_json=doc.content_json,
            change_description=change_desc,
            created_by=actor_id,
        )
        db.add(doc_version)
        db.commit()
        db.refresh(doc_version)
        return doc_version

    def list_versions(self, db: Session, doc_id: str) -> list[DocumentVersionRead]:
        return [self._to_doc_version_read(v) for v in self.doc_version_repo.list_by_document(db, doc_id)]


class ReviewService(BaseService):
    def __init__(self) -> None:
        self.review_task_repo = ReviewTaskRepository()
        self.review_comment_repo = ReviewCommentRepository()
        self.review_checklist_repo = ReviewChecklistRepository()
        self.review_score_repo = ReviewScoreRepository()
        self.audit = AuditService()

    @staticmethod
    def _to_task_read(task: ReviewTask) -> ReviewTaskRead:
        return ReviewTaskRead(
            id=task.id,
            document_id=task.document_id,
            document_version=task.document_version,
            project_id=task.project_id,
            review_type=task.review_type,
            priority=task.priority,
            assignee_ids=task.assignee_ids or [],
            due_date=task.due_date,
            config=task.config_json or {},
            status=task.status,
            result=task.result_json,
            created_by=task.created_by,
        )

    @staticmethod
    def _to_comment_read(comment: ReviewComment) -> ReviewCommentRead:
        return ReviewCommentRead(
            id=comment.id,
            review_task_id=comment.review_task_id,
            document_id=comment.document_id,
            parent_comment_id=comment.parent_comment_id,
            comment_type=comment.comment_type,
            status=comment.status,
            severity=comment.severity,
            line_number=comment.line_number,
            section_path=comment.section_path,
            content=comment.content,
            suggestion=comment.suggestion,
            created_by=comment.created_by,
            resolved_by=comment.resolved_by,
        )

    @staticmethod
    def _to_checklist_read(checklist: ReviewChecklist) -> ReviewChecklistRead:
        return ReviewChecklistRead(
            id=checklist.id,
            review_task_id=checklist.review_task_id,
            doc_type=checklist.doc_type,
            item_key=checklist.item_key,
            item_text=checklist.item_text,
            category=checklist.category,
            sort_order=checklist.sort_order,
            status=checklist.status,
            comment=checklist.comment,
            checked_by=checklist.checked_by,
        )

    @staticmethod
    def _to_score_read(score: ReviewScore) -> ReviewScoreRead:
        return ReviewScoreRead(
            id=score.id,
            review_task_id=score.review_task_id,
            document_id=score.document_id,
            dimension=score.dimension,
            score=score.score,
            weight=score.weight,
            comment=score.comment,
            is_ai=score.is_ai,
            scored_by=score.scored_by,
        )

    def create_review_task(self, db: Session, payload: ReviewTaskCreate, actor_id: str = "user_demo") -> ReviewTaskRead:
        task = ReviewTask(
            id=f"revtask_{uuid4().hex[:12]}",
            document_id=payload.document_id,
            document_version=payload.document_version,
            project_id=payload.project_id,
            status="pending",
            review_type=payload.review_type,
            priority=payload.priority,
            assignee_ids=payload.assignee_ids if payload.assignee_ids else None,
            due_date=payload.due_date,
            config_json=payload.config,
            created_by=actor_id,
        )
        created = self.review_task_repo.add(db, task)

        self.audit.record(
            db,
            actor_id=actor_id,
            action="create_review_task",
            target_type="review_task",
            target_id=created.id,
            request_json=payload.model_dump(),
            response_json=self._to_task_read(created).model_dump(),
        )
        return self._to_task_read(created)

    def update_review_task(self, db: Session, task_id: str, payload: ReviewTaskUpdate, actor_id: str = "user_demo") -> ReviewTaskRead:
        task = self.review_task_repo.get(db, task_id)
        if payload.status is not None:
            task.status = payload.status
        if payload.assignee_ids is not None:
            task.assignee_ids = payload.assignee_ids if payload.assignee_ids else None
        if payload.due_date is not None:
            task.due_date = payload.due_date
        if payload.result is not None:
            task.result_json = payload.result

        db.commit()
        db.refresh(task)

        self.audit.record(
            db,
            actor_id=actor_id,
            action="update_review_task",
            target_type="review_task",
            target_id=task.id,
            request_json=payload.model_dump(exclude_none=True),
            response_json=self._to_task_read(task).model_dump(),
        )
        return self._to_task_read(task)

    def create_comment(self, db: Session, payload: ReviewCommentCreate, actor_id: str = "user_demo") -> ReviewCommentRead:
        comment = ReviewComment(
            id=f"revcomm_{uuid4().hex[:12]}",
            review_task_id=payload.review_task_id,
            document_id=payload.document_id,
            parent_comment_id=payload.parent_comment_id,
            comment_type=payload.comment_type,
            status="open",
            severity=payload.severity,
            line_number=payload.line_number,
            section_path=payload.section_path,
            content=payload.content,
            suggestion=payload.suggestion,
            created_by=actor_id,
        )
        created = self.review_comment_repo.add(db, comment)

        self.audit.record(
            db,
            actor_id=actor_id,
            action="create_review_comment",
            target_type="review_comment",
            target_id=created.id,
            request_json=payload.model_dump(),
            response_json=self._to_comment_read(created).model_dump(),
        )
        return self._to_comment_read(created)

    def update_comment(self, db: Session, comment_id: str, payload: ReviewCommentUpdate, actor_id: str = "user_demo") -> ReviewCommentRead:
        comment = self.review_comment_repo.get(db, comment_id)
        if payload.status is not None:
            comment.status = payload.status
        if payload.content is not None:
            comment.content = payload.content
        if payload.suggestion is not None:
            comment.suggestion = payload.suggestion
        if payload.resolved_by is not None:
            comment.resolved_by = payload.resolved_by

        db.commit()
        db.refresh(comment)

        self.audit.record(
            db,
            actor_id=actor_id,
            action="update_review_comment",
            target_type="review_comment",
            target_id=comment.id,
            request_json=payload.model_dump(exclude_none=True),
            response_json=self._to_comment_read(comment).model_dump(),
        )
        return self._to_comment_read(comment)

    def create_checklist_item(self, db: Session, payload: ReviewChecklistCreate) -> ReviewChecklistRead:
        checklist = ReviewChecklist(
            id=f"revcheck_{uuid4().hex[:12]}",
            review_task_id=payload.review_task_id,
            doc_type=payload.doc_type,
            item_key=payload.item_key,
            item_text=payload.item_text,
            category=payload.category,
            sort_order=payload.sort_order,
            status="pending",
        )
        created = self.review_checklist_repo.add(db, checklist)
        return self._to_checklist_read(created)

    def update_checklist_item(
        self, db: Session, checklist_id: str, payload: ReviewChecklistUpdate, actor_id: str = "user_demo"
    ) -> ReviewChecklistRead:
        checklist = self.review_checklist_repo.get(db, checklist_id)
        if payload.status is not None:
            checklist.status = payload.status
        if payload.comment is not None:
            checklist.comment = payload.comment
        if payload.checked_by is not None:
            checklist.checked_by = payload.checked_by
        elif payload.status in ["passed", "failed"]:
            checklist.checked_by = actor_id

        db.commit()
        db.refresh(checklist)
        return self._to_checklist_read(checklist)

    def create_score(self, db: Session, payload: ReviewScoreCreate, actor_id: str = "user_demo") -> ReviewScoreRead:
        score = ReviewScore(
            id=f"revscore_{uuid4().hex[:12]}",
            review_task_id=payload.review_task_id,
            document_id=payload.document_id,
            dimension=payload.dimension,
            score=payload.score,
            weight=payload.weight,
            comment=payload.comment,
            is_ai=payload.is_ai,
            scored_by=actor_id,
        )
        created = self.review_score_repo.add(db, score)
        return self._to_score_read(created)


class CoverageService(BaseService):
    def __init__(self) -> None:
        self.snapshot_repo = CoverageSnapshotRepository()
        self.metric_repo = CoverageMetricRepository()
        self.audit = AuditService()

    @staticmethod
    def _to_snapshot_read(snapshot: CoverageSnapshot) -> CoverageSnapshotRead:
        return CoverageSnapshotRead(
            id=snapshot.id,
            project_id=snapshot.project_id,
            execution_id=snapshot.execution_id,
            commit_sha=snapshot.commit_sha,
            branch=snapshot.branch,
            tool_name=snapshot.tool_name,
            report_format=snapshot.report_format,
            summary=snapshot.summary_json,
            created_by=snapshot.created_by,
        )

    @staticmethod
    def _to_metric_read(metric: CoverageMetric) -> CoverageMetricRead:
        return CoverageMetricRead(
            id=metric.id,
            snapshot_id=metric.snapshot_id,
            metric_type=metric.metric_type,
            package_name=metric.package_name,
            file_path=metric.file_path,
            covered=metric.covered,
            total=metric.total,
            missed=metric.missed,
            percentage=metric.percentage,
        )

    def create_snapshot(self, db: Session, payload: CoverageSnapshotCreate, actor_id: str = "user_demo") -> CoverageSnapshotRead:
        snapshot = CoverageSnapshot(
            id=f"covsnap_{uuid4().hex[:12]}",
            project_id=payload.project_id,
            execution_id=payload.execution_id,
            commit_sha=payload.commit_sha,
            branch=payload.branch,
            tool_name=payload.tool_name,
            report_format=payload.report_format,
            summary_json=payload.summary,
            created_by=actor_id,
        )
        created = self.snapshot_repo.add(db, snapshot)

        self.audit.record(
            db,
            actor_id=actor_id,
            action="create_coverage_snapshot",
            target_type="coverage_snapshot",
            target_id=created.id,
            request_json=payload.model_dump(),
            response_json=self._to_snapshot_read(created).model_dump(),
        )
        return self._to_snapshot_read(created)

    def get_snapshot(self, db: Session, snapshot_id: str) -> CoverageSnapshotRead:
        return self._to_snapshot_read(self.snapshot_repo.get(db, snapshot_id))

    def list_snapshots(self, db: Session, project_id: str) -> list[CoverageSnapshotRead]:
        return [self._to_snapshot_read(s) for s in self.snapshot_repo.list_by_project(db, project_id)]

    def create_metric(self, db: Session, payload: CoverageMetricCreate) -> CoverageMetricRead:
        metric = CoverageMetric(
            id=f"covmet_{uuid4().hex[:12]}",
            snapshot_id=payload.snapshot_id,
            metric_type=payload.metric_type,
            package_name=payload.package_name,
            file_path=payload.file_path,
            covered=payload.covered,
            total=payload.total,
            missed=payload.missed,
            percentage=payload.percentage,
        )
        created = self.metric_repo.add(db, metric)
        return self._to_metric_read(created)

    def list_metrics(self, db: Session, snapshot_id: str) -> list[CoverageMetricRead]:
        return [self._to_metric_read(m) for m in self.metric_repo.list_by_snapshot(db, snapshot_id)]
