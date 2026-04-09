from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_insight import AiInsight
from app.schemas.query import ListQueryParams
from app.schemas.ai import AiRequest, AiResponse
from app.services.base import BaseService
from app.schemas.ai import AiHistoryItem
from app.utils.time import utcnow
from app.services.query_filters import (
    apply_case_insensitive_filter,
    apply_contains_filter,
    apply_pagination,
)


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
        query: ListQueryParams,
        limit: int | None = None,
    ) -> list[AiHistoryItem]:
        stmt = select(AiInsight).order_by(AiInsight.id.desc())
        stmt = apply_case_insensitive_filter(stmt, AiInsight.execution_id, query.execution_id)
        stmt = apply_case_insensitive_filter(stmt, AiInsight.model_name, query.model_name)
        stmt = apply_case_insensitive_filter(stmt, AiInsight.insight_type, query.insight_type)
        stmt = apply_contains_filter(
            stmt,
            [
                AiInsight.id,
                AiInsight.execution_id,
                AiInsight.insight_type,
                AiInsight.model_name,
                AiInsight.prompt_version,
                func.coalesce(func.json_extract(AiInsight.input_json, "$.input_text"), ""),
                func.coalesce(func.json_extract(AiInsight.input_json, "$.context.execution_id"), ""),
                func.coalesce(func.json_extract(AiInsight.output_json, "$.summary"), ""),
                func.coalesce(func.json_extract(AiInsight.output_json, "$.notes"), ""),
            ],
            query.search,
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        else:
            stmt = apply_pagination(stmt, page=query.page, page_size=query.page_size)
        insights = list(db.scalars(stmt).all())
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
