from app.workers.celery_app import celery_app


@celery_app.task(name="aiqahub.execution.run")
def run_execution(execution_id: str) -> dict[str, str]:
    return {"execution_id": execution_id, "status": "queued"}

