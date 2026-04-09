from typing import Any

from app.db.session import SessionLocal
from app.services.execution_service import ExecutionService
from app.workers.celery_app import celery_app


def _final_status_for_execution(execution_id: str) -> str:
    _ = execution_id
    return "success"


def _build_summary(final_status: str) -> dict[str, Any]:
    if final_status == "success":
        return {"passed": 3, "failed": 0, "success_rate": 100.0}
    if final_status == "failed":
        return {"passed": 2, "failed": 1, "success_rate": 66.7}
    raise ValueError(f"invalid final status: {final_status}")


def _build_step_plan(request_params: dict[str, Any] | None) -> list[dict[str, Any]]:
    default_steps = [
        {"task_key": "prepare", "task_name": "Prepare Context", "input_json": {"phase": "prepare"}},
        {"task_key": "execute", "task_name": "Execute Checks", "input_json": {"phase": "execute"}},
        {"task_key": "collect", "task_name": "Collect Artifacts", "input_json": {"phase": "collect"}},
    ]
    params = request_params or {}
    raw_steps = params.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        return default_steps

    normalized_steps: list[dict[str, Any]] = []
    for index, raw_step in enumerate(raw_steps, start=1):
        if not isinstance(raw_step, dict):
            continue
        task_key = str(raw_step.get("task_key") or raw_step.get("key") or f"step_{index}")
        task_name = str(raw_step.get("task_name") or raw_step.get("name") or task_key.replace("_", " ").title())
        input_json = raw_step.get("input_json")
        if input_json is None:
            input_json = raw_step.get("input") or {}
        normalized_steps.append(
            {
                "task_key": task_key,
                "task_name": task_name,
                "input_json": input_json,
            }
        )
    return normalized_steps or default_steps


@celery_app.task(name="aiqahub.execution.run")
def run_execution(execution_id: str) -> dict[str, Any]:
    service = ExecutionService()
    with SessionLocal() as db:
        execution = service.repo.get(db, execution_id)
        service.mark_running(db, execution_id)
        step_plan = _build_step_plan(execution.request_params_json)
        final_status = _final_status_for_execution(execution_id)
        total_steps = len(step_plan)
        passed_steps = 0
        failed_steps = 0

        for index, step in enumerate(step_plan, start=1):
            task = service.create_task(
                db,
                execution_id=execution_id,
                task_key=step["task_key"],
                task_name=step["task_name"],
                task_order=index,
                input_json=step.get("input_json") or {},
            )
            step_status = "failed" if final_status == "failed" and index == total_steps else "success"
            step_output = {
                "execution_id": execution_id,
                "task_key": task.task_key,
                "task_name": task.task_name,
                "task_order": index,
                "status": step_status,
            }
            error_message = None
            if step_status == "failed":
                error_message = f"{task.task_name} failed"
                failed_steps += 1
            else:
                passed_steps += 1
            service.update_task_status(
                db,
                task.id,
                status=step_status,
                output_json=step_output,
                error_message=error_message,
            )
            service.record_artifact(
                db,
                execution_id=execution_id,
                artifact_type="task-log",
                name=f"{index:02d}-{task.task_key}",
                storage_uri=f"memory://executions/{execution_id}/tasks/{task.id}",
            )

        if final_status == "failed" and failed_steps == 0:
            failed_steps = 1
            passed_steps = max(passed_steps - 1, 0)
        summary = _build_summary(final_status)
        if final_status == "success":
            summary = {"passed": passed_steps, "failed": failed_steps, "success_rate": 100.0}
        else:
            total = passed_steps + failed_steps
            success_rate = round((passed_steps / total) * 100, 1) if total else 0.0
            summary = {"passed": passed_steps, "failed": failed_steps, "success_rate": success_rate}
        service.mark_completed(db, execution_id, status=final_status, summary=summary)

    return {
        "execution_id": execution_id,
        "status": final_status,
        "summary": summary,
    }
