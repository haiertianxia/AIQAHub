from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.execution import ExecutionRepository
from app.crud.quality_rule import QualityRuleRepository
from app.models.environment import Environment
from app.models.execution import Execution
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
from app.schemas.governance import GovernanceEventDetailRead, normalize_utc_timestamp, stable_governance_event_id
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

    @staticmethod
    def _as_list(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @staticmethod
    def _rule_config(rule: QualityRule) -> dict:
        return dict(rule.config_json or {})

    def _rule_scope(self, rule: QualityRule) -> dict:
        config = self._rule_config(rule)
        scope = config.get("scope")
        if isinstance(scope, dict):
            return scope
        return {}

    def _rule_project_ids(self, rule: QualityRule) -> list[str]:
        config = self._rule_config(rule)
        scope = self._rule_scope(rule)
        project_ids = self._as_list(scope.get("project_ids") or scope.get("projects") or config.get("project_ids"))
        return project_ids or [rule.project_id]

    def _rule_environment_types(self, rule: QualityRule) -> list[str]:
        config = self._rule_config(rule)
        scope = self._rule_scope(rule)
        return self._as_list(scope.get("environment_types") or scope.get("environments") or config.get("environment_types"))

    def _rule_stages(self, rule: QualityRule) -> list[str]:
        config = self._rule_config(rule)
        scope = self._rule_scope(rule)
        return self._as_list(scope.get("stages") or config.get("stages"))

    def _critical_task_keys(self, rule: QualityRule) -> list[str]:
        config = self._rule_config(rule)
        keys = config.get("critical_task_keys") or config.get("critical_tasks")
        return self._as_list(keys)

    @staticmethod
    def _execution_stage(execution) -> str | None:
        request_params = execution.request_params_json or {}
        summary = execution.summary_json or {}
        stage = request_params.get("stage") or summary.get("stage") or execution.trigger_source
        if stage is None:
            return None
        stage_text = str(stage).strip()
        return stage_text or None

    def _rule_matches_execution(self, rule: QualityRule, execution, env: Environment | None) -> bool:
        if rule.project_id != execution.project_id:
            return False
        project_ids = self._rule_project_ids(rule)
        if project_ids and execution.project_id not in project_ids:
            return False
        environment_types = self._rule_environment_types(rule)
        if environment_types and env is not None and env.env_type not in environment_types:
            return False
        stages = self._rule_stages(rule)
        stage = self._execution_stage(execution)
        if stages and stage is not None and stage not in stages:
            return False
        return True

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
        environment = db.get(Environment, execution.env_id)
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
        applicable_rules = [rule for rule in enabled_rules if self._rule_matches_execution(rule, execution, environment)]
        critical_task_keys = sorted({key for rule in applicable_rules for key in self._critical_task_keys(rule)})
        if critical_task_keys:
            task_map = {task.task_key: task for task in task_rows}
            missing = [key for key in critical_task_keys if key not in task_map]
            failed = [key for key in critical_task_keys if task_map.get(key) is not None and task_map[key].status != "success"]
            if missing or failed:
                reason_parts = []
                if missing:
                    reason_parts.append(f"missing critical tasks: {', '.join(missing)}")
                if failed:
                    reason_parts.append(f"failed critical tasks: {', '.join(failed)}")
                return GateResult(
                    execution_id=execution.id,
                    result="FAIL",
                    score=int(round(success_rate)),
                    reason="; ".join(reason_parts),
                    task_count=task_count,
                    failed_tasks=failed_tasks,
                    task_threshold=0,
                    completion_source=completion_source,
                )
        thresholds = [
            float((rule.config_json or {}).get("min_success_rate", 95))
            for rule in applicable_rules
            if rule.rule_type == "success_rate"
        ]
        threshold = min(thresholds) if thresholds else 95.0
        task_thresholds = [
            int((rule.config_json or {}).get("min_task_count", 3))
            for rule in applicable_rules
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

    @staticmethod
    def _revision_event(revision: QualityRuleRevision, *, now: datetime | None = None) -> GovernanceEventDetailRead:
        source_id = revision.id
        return GovernanceEventDetailRead(
            id=stable_governance_event_id("gate_change", "quality_rule_revision", source_id),
            kind="gate_change",
            source_type="quality_rule_revision",
            source_id=source_id,
            timestamp=normalize_utc_timestamp(now or datetime.now(UTC)),
            severity="info",
            target_type="quality_rule",
            target_id=revision.rule_id,
            title=f"Gate rule {revision.action}",
            description=f"rule={revision.rule_id} version={revision.version}",
            metadata={
                "rule_id": revision.rule_id,
                "version": revision.version,
                "action": revision.action,
            },
            raw={
                "before_json": revision.before_json or {},
                "after_json": revision.after_json or {},
            },
        )

    @staticmethod
    def _execution_failed_event(execution: Execution) -> GovernanceEventDetailRead:
        summary = dict(execution.summary_json or {})
        source_id = execution.id
        timestamp = (
            summary.get("completed_at")
            or summary.get("timed_out_at")
            or summary.get("started_at")
        )
        status = str(execution.status or "unknown").lower()
        return GovernanceEventDetailRead(
            id=stable_governance_event_id("gate_fail", "execution", source_id),
            kind="gate_fail",
            source_type="execution",
            source_id=source_id,
            timestamp=normalize_utc_timestamp(timestamp),
            severity="error",
            status=status,
            target_type="execution",
            target_id=source_id,
            project_id=execution.project_id,
            title=f"Gate failure candidate: {execution.id}",
            description=f"execution status={status}",
            metadata={
                "env_id": execution.env_id,
                "suite_id": execution.suite_id,
                "completion_source": summary.get("completion_source"),
            },
            raw=summary,
        )

    def list_governance_events(self, db: Session, *, now: datetime | None = None) -> list[GovernanceEventDetailRead]:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        revisions = list(db.scalars(select(QualityRuleRevision)).all())
        failed_executions = list(
            db.scalars(select(Execution).where(Execution.status.in_(["failed", "timeout"]))).all()
        )
        events: list[GovernanceEventDetailRead] = []
        events.extend(self._revision_event(revision, now=current) for revision in revisions)
        events.extend(self._execution_failed_event(execution) for execution in failed_executions)
        return events
