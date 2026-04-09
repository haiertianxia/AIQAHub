from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai import AiHistoryItem, AiRequest, AiResponse
from app.services.ai_service import AIService

router = APIRouter()
service = AIService()


@router.post("/analyze", response_model=AiResponse)
def analyze(payload: AiRequest, db: Session = Depends(get_db)) -> AiResponse:
    return service.analyze(db, payload)


@router.get("/history", response_model=list[AiHistoryItem])
def history(db: Session = Depends(get_db), limit: int = Query(default=20, ge=1, le=100)) -> list[AiHistoryItem]:
    return service.list_history(db, limit=limit)
