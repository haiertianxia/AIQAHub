from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.query import ListQueryParams
from app.schemas.ai import AiHistoryItem, AiRequest, AiResponse
from app.services.ai_service import AIService

router = APIRouter()
service = AIService()


@router.post("/analyze", response_model=AiResponse)
def analyze(payload: AiRequest, db: Session = Depends(get_db)) -> AiResponse:
    return service.analyze(db, payload)


@router.get("/history", response_model=list[AiHistoryItem])
def history(
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, ge=1, le=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    execution_id: str | None = Query(default=None),
    model_name: str | None = Query(default=None),
    insight_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> list[AiHistoryItem]:
    query = ListQueryParams(
        search=search,
        execution_id=execution_id,
        model_name=model_name,
        insight_type=insight_type,
        page=page,
        page_size=page_size,
    )
    return service.list_history(db, query=query, limit=limit)
