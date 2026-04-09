from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_insight import AiInsight
from app.schemas.ai import AiRequest, AiResponse
from app.services.base import BaseService
from app.schemas.ai import AiHistoryItem


class AIService(BaseService):
    def _resolve_execution_id(self, payload: AiRequest) -> str:
        context = payload.context or {}
        for key in ("execution_id", "report_execution_id", "analysis_execution_id"):
            value = context.get(key)
            if isinstance(value, str) and value:
                return value
        return f"ai_{uuid4().hex[:12]}"

    def analyze(self, db: Session, payload: AiRequest) -> AiResponse:
        execution_id = self._resolve_execution_id(payload)
        output = {
            "summary": f"analyzed: {payload.input_text}",
            "suggestions": ["check regression scope", "review failure clustering"],
            "context": payload.context,
        }
        insight = AiInsight(
            id=f"ai_{uuid4().hex[:12]}",
            execution_id=execution_id,
            insight_type="analysis",
            model_name="mock-llm",
            prompt_version="v1",
            confidence=0.75,
            input_json=payload.model_dump(),
            output_json=output,
        )
        db.add(insight)
        db.commit()
        return AiResponse(
            model="mock-llm",
            confidence=0.75,
            result=output,
        )

    def list_history(self, db: Session, *, limit: int = 20) -> list[AiHistoryItem]:
        insights = list(db.scalars(select(AiInsight).order_by(AiInsight.id.desc()).limit(limit)).all())
        return [
            AiHistoryItem(
                id=insight.id,
                execution_id=insight.execution_id,
                insight_type=insight.insight_type,
                model_name=insight.model_name,
                prompt_version=insight.prompt_version,
                confidence=insight.confidence,
                input_json=insight.input_json or {},
                output_json=insight.output_json or {},
            )
            for insight in insights
        ]
