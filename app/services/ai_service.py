from app.schemas.ai import AiRequest, AiResponse
from app.services.base import BaseService


class AIService(BaseService):
    def analyze(self, payload: AiRequest) -> AiResponse:
        return AiResponse(
            model="mock-llm",
            confidence=0.75,
            result={
                "summary": f"analyzed: {payload.input_text}",
                "suggestions": ["check regression scope", "review failure clustering"],
            },
        )

