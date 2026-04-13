from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.connectors.llm.provider import analyze_with_fallback
from app.core.config import get_settings
from app.models.ai_insight import AiInsight
from app.schemas.query import ListQueryParams
from app.schemas.ai import AiRequest, AiResponse
from app.services.base import BaseService
from app.schemas.ai import AiHistoryItem
from app.utils.time import utcnow
from app.services.audit_service import AuditService
from app.services.query_filters import (
    apply_case_insensitive_filter,
    apply_contains_filter,
    apply_json_path_filter,
    apply_pagination,
    apply_sort,
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
        settings = get_settings()
        insight_id = f"ai_z{utcnow().strftime('%Y%m%d%H%M%S%f')}_{uuid4().hex[:8]}"
        analysis = analyze_with_fallback(settings.ai_provider, settings.ai_model_name, payload.input_text, payload.context or {})
        output = {
            "provider": analysis["provider"],
            "model": analysis["model"],
            "summary": analysis["summary"],
            "suggestions": analysis["suggestions"],
            "context": analysis["context"],
            "fallback_from": analysis.get("fallback_from"),
            "fallback_reason": analysis.get("fallback_reason"),
        }
        insight = AiInsight(
            id=insight_id,
            execution_id=execution_id,
            insight_type="analysis",
            model_name=analysis["model"],
            prompt_version="v1",
            confidence=float(analysis["confidence"]),
            input_json=payload.model_dump(),
            output_json=output,
        )
        db.add(insight)
        db.commit()
        AuditService().record(
            db,
            actor_id=None,
            action="analyze_ai",
            target_type="ai_insight",
            target_id=insight_id,
            request_json=payload.model_dump(),
            response_json=output,
        )
        return AiResponse(
            model=analysis["model"],
            confidence=float(analysis["confidence"]),
            result=output,
        )

    def list_history(
        self,
        db: Session,
        *,
        query: ListQueryParams,
        limit: int | None = None,
    ) -> list[AiHistoryItem]:
        stmt = select(AiInsight)
        stmt = apply_case_insensitive_filter(stmt, AiInsight.execution_id, query.execution_id)
        stmt = apply_case_insensitive_filter(stmt, AiInsight.model_name, query.model_name)
        stmt = apply_json_path_filter(stmt, AiInsight.output_json, "$.provider", query.provider_name)
        stmt = apply_case_insensitive_filter(stmt, AiInsight.insight_type, query.insight_type)
        stmt = apply_contains_filter(
            stmt,
            [
                AiInsight.id,
                AiInsight.execution_id,
                AiInsight.insight_type,
                AiInsight.model_name,
                func.coalesce(func.json_extract(AiInsight.output_json, "$.provider"), ""),
                AiInsight.prompt_version,
                func.coalesce(func.json_extract(AiInsight.input_json, "$.input_text"), ""),
                func.coalesce(func.json_extract(AiInsight.input_json, "$.context.execution_id"), ""),
                func.coalesce(func.json_extract(AiInsight.output_json, "$.summary"), ""),
                func.coalesce(func.json_extract(AiInsight.output_json, "$.notes"), ""),
            ],
            query.search,
        )
        stmt = apply_sort(
            stmt,
            sort=query.sort,
            allowed={
                "id": AiInsight.id,
                "execution_id": AiInsight.execution_id,
                "model_name": AiInsight.model_name,
                "insight_type": AiInsight.insight_type,
                "confidence": AiInsight.confidence,
            },
            default="-id",
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
                provider_name=str((insight.output_json or {}).get("provider") or "mock"),
                prompt_version=insight.prompt_version,
                confidence=insight.confidence,
                input_json=insight.input_json or {},
                output_json=insight.output_json or {},
            )
            for insight in insights
        ]
