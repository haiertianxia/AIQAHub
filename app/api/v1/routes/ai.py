from fastapi import APIRouter

from app.schemas.ai import AiRequest, AiResponse
from app.services.ai_service import AIService

router = APIRouter()
service = AIService()


@router.post("/analyze", response_model=AiResponse)
def analyze(payload: AiRequest) -> AiResponse:
    return service.analyze(payload)

