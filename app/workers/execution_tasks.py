from typing import Any

from app.db.session import SessionLocal
from app.services.execution_service import ExecutionService
from app.workers.celery_app import celery_app


def _final_status_for_execution(execution_id: str) -> str:
    _ = execution_id
    return "success"


def _build_summary(final_status: str) -> dict[str, Any]:
    if final_status == "success":
        return {"passed": 1, "failed": 0, "success_rate": 100.0}
    if final_status == "failed":
        return {"passed": 0, "failed": 1, "success_rate": 0.0}
    raise ValueError(f"invalid final status: {final_status}")


@celery_app.task(name="aiqahub.execution.run")
def run_execution(execution_id: str) -> dict[str, Any]:
    service = ExecutionService()
    with SessionLocal() as db:
        service.mark_running(db, execution_id)
        final_status = _final_status_for_execution(execution_id)
        summary = _build_summary(final_status)
        service.mark_completed(db, execution_id, status=final_status, summary=summary)

    return {
        "execution_id": execution_id,
        "status": final_status,
        "summary": summary,
    }
