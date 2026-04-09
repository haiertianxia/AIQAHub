import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_insight import AiInsight
from app.schemas.ai import AiRequest, AiResponse
from app.services.base import BaseService
from app.schemas.ai import AiHistoryItem
from app.utils.time import utcnow


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
        insight_id = f"ai_z{utcnow().strftime('%Y%m%d%H%M%S%f')}_{uuid4().hex[:8]}"
        output = {
            "summary": f"analyzed: {payload.input_text}",
            "suggestions": ["check regression scope", "review failure clustering"],
            "context": payload.context,
        }
        insight = AiInsight(
            id=insight_id,
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

    def list_history(
        self,
        db: Session,
        *,
        limit: int | None = None,
        page: int = 1,
        page_size: int = 20,
        execution_id: str | None = None,
        model_name: str | None = None,
        insight_type: str | None = None,
        search: str | None = None,
    ) -> list[AiHistoryItem]:
        stmt = select(AiInsight)
        if execution_id:
            stmt = stmt.where(AiInsight.execution_id == execution_id)
        if model_name:
            stmt = stmt.where(AiInsight.model_name == model_name)
        if insight_type:
            stmt = stmt.where(AiInsight.insight_type == insight_type)
        insights = list(db.scalars(stmt.order_by(AiInsight.id.desc())).all())
        if search:
            lowered = search.strip().lower()

            def to_text(value: object) -> str:
                return json.dumps(value, ensure_ascii=False, sort_keys=True) if value is not None else ""

            def matches(insight: AiInsight) -> bool:
                haystack = " ".join(
                    [
                        insight.execution_id,
                        insight.insight_type,
                        insight.model_name,
                        insight.prompt_version,
                        to_text(insight.input_json),
                        to_text(insight.output_json),
                    ],
                ).lower()
                return lowered in haystack

            insights = [insight for insight in insights if matches(insight)]
        if limit is not None:
            insights = insights[:limit]
        else:
            start = max(page - 1, 0) * page_size
            insights = insights[start : start + page_size]
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
