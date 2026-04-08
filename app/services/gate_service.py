from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.execution import ExecutionRepository
from app.crud.quality_rule import QualityRuleRepository
from app.services.audit_service import AuditService
from app.models.quality_rule import QualityRule
from app.schemas.gate import GateEvaluateRequest, GateResult, QualityRuleCreate, QualityRuleRead, QualityRuleUpdate
from app.services.base import BaseService


class GateService(BaseService):
    def __init__(self) -> None:
        self.rule_repo = QualityRuleRepository()
        self.execution_repo = ExecutionRepository()
        self.audit = AuditService()

    @staticmethod
    def _to_read(rule: QualityRule) -> QualityRuleRead:
        return QualityRuleRead(
            id=rule.id,
            project_id=rule.project_id,
            name=rule.name,
            rule_type=rule.rule_type,
            enabled=rule.enabled,
            config=rule.config_json or {},
        )

    def list_rules(self, db: Session) -> list[QualityRuleRead]:
        return [self._to_read(rule) for rule in self.rule_repo.list(db)]

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
        if success_rate >= threshold:
            result = "PASS"
        elif success_rate >= threshold - 10:
            result = "WARN"
        else:
            result = "FAIL"
        return GateResult(
            execution_id=execution.id,
            result=result,
            score=int(round(success_rate)),
            reason=f"success_rate={success_rate:.1f}, threshold={threshold:.1f}",
        )
