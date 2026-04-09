from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.execution import ExecutionRepository
from app.crud.quality_rule import QualityRuleRepository
from app.models.quality_rule_revision import QualityRuleRevision
from app.services.audit_service import AuditService
from app.models.execution_task import ExecutionTask
from app.models.quality_rule import QualityRule
from app.schemas.gate import (
    GateEvaluateRequest,
    GateResult,
    QualityRuleCreate,
    QualityRuleRead,
    QualityRuleRevisionRead,
    QualityRuleUpdate,
)
from app.services.base import BaseService


class GateService(BaseService):
    def __init__(self) -> None:
        self.rule_repo = QualityRuleRepository()
        self.execution_repo = ExecutionRepository()
        self.audit = AuditService()

    @staticmethod
    def _to_read(rule: QualityRule, version: int = 1) -> QualityRuleRead:
        return QualityRuleRead(
            id=rule.id,
            project_id=rule.project_id,
            name=rule.name,
            rule_type=rule.rule_type,
            enabled=rule.enabled,
            config=rule.config_json or {},
            version=version,
        )

    @staticmethod
    def _to_revision_read(revision: QualityRuleRevision) -> QualityRuleRevisionRead:
        return QualityRuleRevisionRead(
            id=revision.id,
            rule_id=revision.rule_id,
            version=revision.version,
            action=revision.action,
            before_json=revision.before_json,
            after_json=revision.after_json,
        )

    def _next_version(self, db: Session, rule_id: str) -> int:
        statement = select(QualityRuleRevision.version).where(QualityRuleRevision.rule_id == rule_id)
        versions = list(db.scalars(statement).all())
        return (max(versions) if versions else 0) + 1

    def _record_revision(
        self,
        db: Session,
        *,
        rule_id: str,
        action: str,
        before_json: dict | None,
        after_json: dict | None,
    ) -> QualityRuleRevisionRead:
        revision = QualityRuleRevision(
            id=f"qrr_{uuid4().hex[:12]}",
            rule_id=rule_id,
            version=self._next_version(db, rule_id),
            action=action,
            before_json=before_json,
            after_json=after_json,
        )
        db.add(revision)
        db.commit()
        db.refresh(revision)
        return self._to_revision_read(revision)

    def list_rules(self, db: Session) -> list[QualityRuleRead]:
        revisions = {
            revision.rule_id: revision.version
            for revision in db.scalars(select(QualityRuleRevision).order_by(QualityRuleRevision.id.desc())).all()
        }
        return [self._to_read(rule, revisions.get(rule.id, 1)) for rule in self.rule_repo.list(db)]

    def list_rule_history(self, db: Session, rule_id: str) -> list[QualityRuleRevisionRead]:
        statement = select(QualityRuleRevision).where(QualityRuleRevision.rule_id == rule_id).order_by(
            QualityRuleRevision.version.desc()
        )
        return [self._to_revision_read(revision) for revision in db.scalars(statement).all()]

    def create_rule(self, db: Session, payload: QualityRuleCreate) -> QualityRuleRead:
        rule = QualityRule(
            id=f"rule_{uuid4().hex[:12]}",
            project_id=payload.project_id,
            name=payload.name,
            rule_type=payload.rule_type,
            enabled=payload.enabled,
            config_json=payload.config,
        )
        created = self.rule_repo.add(db, rule)
        self._record_revision(
            db,
            rule_id=created.id,
            action="create",
            before_json=None,
            after_json=self._to_read(created, 1).model_dump(),
        )
        self.audit.record(
            db,
            actor_id="user_demo",
            action="create_quality_rule",
            target_type="quality_rule",
            target_id=created.id,
            request_json=payload.model_dump(),
            response_json=self._to_read(created).model_dump(),
        )
        return self._to_read(created)

    def update_rule(self, db: Session, rule_id: str, payload: QualityRuleUpdate) -> QualityRuleRead:
        rule = self.rule_repo.get(db, rule_id)
        if payload.name is not None:
            rule.name = payload.name
        if payload.rule_type is not None:
            rule.rule_type = payload.rule_type
        if payload.enabled is not None:
            rule.enabled = payload.enabled
        if payload.config is not None:
            rule.config_json = payload.config
        db.commit()
        db.refresh(rule)
        version = self._next_version(db, rule.id)
        self._record_revision(
            db,
            rule_id=rule.id,
            action="update",
            before_json=self._to_read(rule, max(version - 1, 1)).model_dump(),
            after_json=self._to_read(rule, version).model_dump(),
        )
        self.audit.record(
            db,
            actor_id="user_demo",
            action="update_quality_rule",
            target_type="quality_rule",
            target_id=rule.id,
            request_json=payload.model_dump(exclude_none=True),
            response_json=self._to_read(rule).model_dump(),
        )
        return self._to_read(rule)

    def delete_rule(self, db: Session, rule_id: str) -> None:
        rule = self.rule_repo.get(db, rule_id)
        self._record_revision(
            db,
            rule_id=rule.id,
            action="delete",
            before_json=self._to_read(rule, self._next_version(db, rule.id)).model_dump(),
            after_json=None,
        )
        db.delete(rule)
        db.commit()
        self.audit.record(
            db,
            actor_id="user_demo",
            action="delete_quality_rule",
            target_type="quality_rule",
            target_id=rule_id,
        )

    def evaluate(self, db: Session, payload: GateEvaluateRequest) -> GateResult:
        execution = self.execution_repo.get(db, payload.execution_id)
        summary = execution.summary_json or {}
        success_rate = float(summary.get("success_rate", 0))
        completion_source = str(summary.get("completion_source") or "unknown")
        if execution.status == "timeout" or completion_source in {"timeout_sweeper", "poller_exhausted"}:
            task_rows = list(db.scalars(select(ExecutionTask).where(ExecutionTask.execution_id == execution.id)).all())
            task_count = len(task_rows)
            failed_tasks = sum(1 for task in task_rows if task.status == "failed")
            return GateResult(
                execution_id=execution.id,
                result="FAIL",
                score=0,
                reason=f"execution timed out via {completion_source}; task_count={task_count}, failed_tasks={failed_tasks}",
                task_count=task_count,
                failed_tasks=failed_tasks,
                task_threshold=0,
                completion_source=completion_source,
            )
        task_rows = list(db.scalars(select(ExecutionTask).where(ExecutionTask.execution_id == execution.id)).all())
        task_count = len(task_rows)
        failed_tasks = sum(1 for task in task_rows if task.status == "failed")
        enabled_rules = list(
            db.scalars(
                select(QualityRule).where(
                    QualityRule.enabled.is_(True),
                    QualityRule.project_id == execution.project_id,
                )
            ).all()
        )
        thresholds = [
            float((rule.config_json or {}).get("min_success_rate", 95))
            for rule in enabled_rules
            if rule.rule_type == "success_rate"
        ]
        threshold = min(thresholds) if thresholds else 95.0
        task_thresholds = [
            int((rule.config_json or {}).get("min_task_count", 3))
            for rule in enabled_rules
            if rule.rule_type == "task_count"
        ]
        task_threshold = max(task_thresholds) if task_thresholds else 3
        if failed_tasks > 0:
            result = "FAIL"
        elif task_count < task_threshold:
            result = "WARN" if success_rate >= threshold else "FAIL"
        elif success_rate >= threshold:
            result = "PASS"
        elif success_rate >= threshold - 10:
            result = "WARN"
        else:
            result = "FAIL"
        return GateResult(
            execution_id=execution.id,
            result=result,
            score=int(round(success_rate)),
            reason=(
                f"success_rate={success_rate:.1f}, threshold={threshold:.1f}, "
                f"task_count={task_count}, task_threshold={task_threshold}, failed_tasks={failed_tasks}"
            ),
            task_count=task_count,
            failed_tasks=failed_tasks,
            task_threshold=task_threshold,
            completion_source=completion_source,
        )
