from app.workers.celery_app import celery_app


@celery_app.task(name="aiqahub.report.build")
def build_report(execution_id: str) -> dict[str, str]:
    return {"execution_id": execution_id, "report_status": "built"}

