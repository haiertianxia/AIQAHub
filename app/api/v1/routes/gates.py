from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.gate import (
    GateEvaluateRequest,
    GateResult,
    QualityRuleCreate,
    QualityRuleRead,
    QualityRuleRevisionRead,
    QualityRuleUpdate,
)
from app.services.gate_service import GateService

router = APIRouter()
service = GateService()


@router.get("/rules", response_model=list[QualityRuleRead])
def list_rules(db: Session = Depends(get_db)) -> list[QualityRuleRead]:
    return service.list_rules(db)


@router.post("/rules", response_model=QualityRuleRead)
def create_rule(payload: QualityRuleCreate, db: Session = Depends(get_db)) -> QualityRuleRead:
    return service.create_rule(db, payload)


@router.put("/rules/{rule_id}", response_model=QualityRuleRead)
def update_rule(rule_id: str, payload: QualityRuleUpdate, db: Session = Depends(get_db)) -> QualityRuleRead:
    return service.update_rule(db, rule_id, payload)


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: str, db: Session = Depends(get_db)) -> None:
    service.delete_rule(db, rule_id)


@router.get("/rules/{rule_id}/history", response_model=list[QualityRuleRevisionRead])
def list_rule_history(rule_id: str, db: Session = Depends(get_db)) -> list[QualityRuleRevisionRead]:
    return service.list_rule_history(db, rule_id)


@router.post("/evaluate", response_model=GateResult)
def evaluate_gate(payload: GateEvaluateRequest, db: Session = Depends(get_db)) -> GateResult:
    return service.evaluate(db, payload)
