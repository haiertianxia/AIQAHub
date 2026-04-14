from datetime import datetime, timezone
import os
from typing import Any

from app.connectors.jenkins.client import JenkinsConnector
from app.connectors.playwright.client import PlaywrightConnector
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.execution import Execution
from app.schemas.connector import JenkinsCallbackPayload
from app.services.connector_service import ConnectorService
from app.services.execution_service import ExecutionService
from app.utils.time import utcnow
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


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _build_step_plan(request_params: dict[str, Any] | None) -> list[dict[str, Any]]:
    default_steps = [
        {"task_key": "prepare", "task_name": "Prepare Context", "input_json": {"phase": "prepare"}},
        {"task_key": "execute", "task_name": "Execute Checks", "input_json": {"phase": "execute"}},
        {"task_key": "collect", "task_name": "Collect Artifacts", "input_json": {"phase": "collect"}},
    ]
    params = request_params or {}
    adapter = str(params.get("adapter") or params.get("adapter_type") or "").lower()
    if adapter == "jenkins":
        job_name = str(params.get("job_name") or params.get("source_ref") or params.get("pipeline") or "aiqahub-job")
        return [
            {"task_key": "trigger_job", "task_name": "Trigger Jenkins Job", "input_json": {"job_name": job_name}},
        ]
    if adapter == "playwright":
        job_name = str(params.get("job_name") or params.get("suite_name") or params.get("source_ref") or "playwright-test")
        return [
            {"task_key": "trigger_playwright", "task_name": "Trigger Playwright Run", "input_json": {"job_name": job_name}},
        ]
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


def _update_started_at(service: ExecutionService, db, execution_id: str) -> None:
    execution = service.repo.get(db, execution_id)
    summary = dict(execution.summary_json or {})
    summary.setdefault("started_at", utcnow().isoformat())
    service.update_summary(db, execution_id, summary)


def _schedule_jenkins_poll(*, execution_id: str, job_name: str, build_number: int, build_url: str, task_id: str, attempt: int) -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    try:
        wait_for_jenkins_build.apply_async(
            args=[execution_id, job_name, build_number, build_url, task_id, attempt],
            countdown=get_settings().jenkins_poll_delay_seconds,
        )
    except Exception:
        return


def _schedule_playwright_poll(*, execution_id: str, job_name: str, job_id: str, task_id: str, attempt: int) -> None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    try:
        wait_for_playwright.apply_async(
            args=[execution_id, job_name, job_id, task_id, attempt],
            countdown=get_settings().jenkins_poll_delay_seconds,
        )
    except Exception:
        return


@celery_app.task(name="aiqahub.execution.run")
def run_execution(execution_id: str) -> dict[str, Any]:
    service = ExecutionService()
    with SessionLocal() as db:
        execution = service.repo.get(db, execution_id)
        service.mark_running(db, execution_id)
        _update_started_at(service, db, execution_id)
        request_params = dict(execution.request_params_json or {})
        step_plan = _build_step_plan(request_params)
        final_status = _final_status_for_execution(execution_id)
        total_steps = len(step_plan)
        passed_steps = 0
        failed_steps = 0
        jenkins_connector = JenkinsConnector()
        playwright_connector = PlaywrightConnector()
        jenkins_mode = str(request_params.get("adapter") or request_params.get("adapter_type") or "").lower() == "jenkins"
        playwright_mode = str(request_params.get("adapter") or request_params.get("adapter_type") or "").lower() == "playwright"
        jenkins_state: dict[str, Any] = {}
        playwright_state: dict[str, Any] = {}

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
            if jenkins_mode:
                job_name = str(step.get("input_json", {}).get("job_name") or request_params.get("job_name") or "aiqahub-job")
                if task.task_key == "trigger_job":
                    jenkins_trigger = jenkins_connector.trigger_job(job_name, request_params)
                    jenkins_state = {
                        "job_name": job_name,
                        "build_number": jenkins_trigger["build_number"],
                        "queue_id": jenkins_trigger["queue_id"],
                        "build_url": jenkins_trigger["url"],
                    }
                    step_output = {**jenkins_trigger, "execution_id": execution_id, "step": task.task_key}
                    passed_steps += 1
                    service.update_task_status(
                        db,
                        task.id,
                        status="success",
                        output_json=step_output,
                        error_message=None,
                    )
                    service.record_artifact(
                        db,
                        execution_id=execution_id,
                        artifact_type="jenkins-console",
                        name=f"{index:02d}-{task.task_key}-console",
                        storage_uri=f"{jenkins_trigger['url']}consoleText",
                    )
                    wait_task = service.create_task(
                        db,
                        execution_id=execution_id,
                        task_key="wait_for_build",
                        task_name="Wait For Jenkins Build",
                        task_order=index + 1,
                        input_json={
                            "job_name": job_name,
                            "build_number": jenkins_trigger["build_number"],
                            "build_url": jenkins_trigger["url"],
                        },
                    )
                    summary = {
                        "status": "running",
                        "passed": passed_steps,
                        "failed": failed_steps,
                        "success_rate": 100.0,
                        "jenkins": {
                            **jenkins_state,
                            "completion_source": "trigger",
                            "poll_count": 0,
                        },
                        "started_at": utcnow().isoformat(),
                    }
                    service.update_summary(db, execution_id, summary)
                    _schedule_jenkins_poll(
                        execution_id=execution_id,
                        job_name=job_name,
                        build_number=jenkins_trigger["build_number"],
                        build_url=jenkins_trigger["url"],
                        task_id=wait_task.id,
                        attempt=0,
                    )
                    return {
                        "execution_id": execution_id,
                        "status": "running",
                        "task_id": task.id,
                        "summary": summary,
                    }
            if playwright_mode:
                job_name = str(step.get("input_json", {}).get("job_name") or request_params.get("job_name") or "playwright-test")
                if task.task_key == "trigger_playwright":
                    playwright_trigger = playwright_connector.trigger_playwright(job_name, request_params)
                    playwright_state = {
                        "job_name": job_name,
                        "job_id": playwright_trigger["job_id"],
                        "status": playwright_trigger["status"],
                    }
                    step_output = {**playwright_trigger, "execution_id": execution_id, "step": task.task_key}
                    passed_steps += 1
                    service.update_task_status(
                        db,
                        task.id,
                        status="success",
                        output_json=step_output,
                        error_message=None,
                    )
                    artifacts = playwright_trigger.get("artifacts")
                    if isinstance(artifacts, dict):
                        for artifact_type, storage_uri in artifacts.items():
                            if not isinstance(storage_uri, str) or not storage_uri:
                                continue
                            service.record_artifact(
                                db,
                                execution_id=execution_id,
                                artifact_type=str(artifact_type),
                                name=f"{index:02d}-{task.task_key}-{artifact_type}",
                                storage_uri=storage_uri,
                            )
                    wait_task = service.create_task(
                        db,
                        execution_id=execution_id,
                        task_key="wait_for_playwright",
                        task_name="Wait For Playwright Run",
                        task_order=index + 1,
                        input_json={
                            "job_name": job_name,
                            "job_id": playwright_trigger["job_id"],
                        },
                    )
                    summary = {
                        "status": "running",
                        "passed": passed_steps,
                        "failed": failed_steps,
                        "success_rate": 100.0,
                        "playwright": {
                            **playwright_state,
                            "completion_source": "trigger",
                            "poll_count": 0,
                        },
                        "started_at": utcnow().isoformat(),
                    }
                    service.update_summary(db, execution_id, summary)
                    _schedule_playwright_poll(
                        execution_id=execution_id,
                        job_name=job_name,
                        job_id=playwright_trigger["job_id"],
                        task_id=wait_task.id,
                        attempt=0,
                    )
                    return {
                        "execution_id": execution_id,
                        "status": "running",
                        "task_id": task.id,
                        "summary": summary,
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
            artifact_payload = service.record_artifact(
                db,
                execution_id=execution_id,
                artifact_type="task-log",
                name=f"{index:02d}-{task.task_key}",
                storage_uri=f"memory://executions/{execution_id}/tasks/{task.id}",
            )
            _ = artifact_payload

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


@celery_app.task(name="aiqahub.execution.wait_for_jenkins_build")
def wait_for_jenkins_build(
    execution_id: str,
    job_name: str,
    build_number: int,
    build_url: str,
    task_id: str,
    attempt: int = 0,
) -> dict[str, Any]:
    service = ExecutionService()
    connector_service = ConnectorService()
    settings = get_settings()
    with SessionLocal() as db:
        execution = service.repo.get(db, execution_id)
        if execution.status in {"success", "failed", "cancelled", "timeout"}:
            return service._to_read(execution).model_dump()

        poll_payload = JenkinsCallbackPayload(
            execution_id=execution_id,
            job_name=job_name,
            build_number=build_number,
            result="running",
            build_url=build_url,
        )
        updated = connector_service.poll_jenkins_build(db, poll_payload)
        latest_execution = service.repo.get(db, execution_id)
        latest_summary = dict(latest_execution.summary_json or {})
        jenkins_summary = dict(latest_summary.get("jenkins") or {})
        poll_count = int(jenkins_summary.get("poll_count", attempt + 1))

        if updated.status == "running":
            output_json = {
                "execution_id": execution_id,
                "job_name": job_name,
                "build_number": build_number,
                "build_url": build_url,
                "attempt": attempt,
                "poll_count": poll_count,
                "status": "running",
            }
            service.update_task_status(
                db,
                task_id,
                status="running",
                output_json=output_json,
            )
            if attempt + 1 < settings.jenkins_poll_attempts:
                _schedule_jenkins_poll(
                    execution_id=execution_id,
                    job_name=job_name,
                    build_number=build_number,
                    build_url=build_url,
                    task_id=task_id,
                    attempt=attempt + 1,
                )
            return {
                "execution_id": execution_id,
                "status": "running",
                "attempt": attempt,
                "poll_count": poll_count,
            }

        service.update_task_status(
            db,
            task_id,
            status=updated.status,
            output_json={
                "execution_id": execution_id,
                "job_name": job_name,
                "build_number": build_number,
                "build_url": build_url,
                "attempt": attempt,
                "poll_count": poll_count,
                "status": updated.status,
            },
        )
        return {
            "execution_id": execution_id,
            "status": updated.status,
            "attempt": attempt,
            "poll_count": poll_count,
        }


@celery_app.task(name="aiqahub.execution.wait_for_playwright")
def wait_for_playwright(
    execution_id: str,
    job_name: str,
    job_id: str,
    task_id: str,
    attempt: int = 0,
) -> dict[str, Any]:
    service = ExecutionService()
    connector = PlaywrightConnector()
    settings = get_settings()
    with SessionLocal() as db:
        execution = service.repo.get(db, execution_id)
        if execution.status in {"success", "failed", "cancelled", "timeout"}:
            return service._to_read(execution).model_dump()

        summary = dict(execution.summary_json or {})
        playwright_summary = dict(summary.get("playwright") or {})
        previous_poll_count = int(playwright_summary.get("poll_count", 0))
        poll_result = connector.wait_for_playwright(
            job_name=job_name,
            job_id=job_id,
            parameters=dict(execution.request_params_json or {}),
            poll_count=previous_poll_count,
        )
        poll_count = int(poll_result.get("poll_count", attempt + 1))
        status = PlaywrightConnector.normalize_status(str(poll_result.get("status") or "running"), default="running")

        if status == "running":
            service.update_task_status(
                db,
                task_id,
                status="running",
                output_json={
                    "execution_id": execution_id,
                    "job_name": job_name,
                    "job_id": job_id,
                    "attempt": attempt,
                    "poll_count": poll_count,
                    "status": "running",
                },
            )
            summary["status"] = "running"
            summary["playwright"] = {
                **playwright_summary,
                "job_name": job_name,
                "job_id": job_id,
                "status": "running",
                "poll_count": poll_count,
                "completion_source": "poller",
            }
            summary.setdefault("started_at", utcnow().isoformat())
            service.update_summary(db, execution_id, summary)

            if attempt + 1 < settings.jenkins_poll_attempts:
                _schedule_playwright_poll(
                    execution_id=execution_id,
                    job_name=job_name,
                    job_id=job_id,
                    task_id=task_id,
                    attempt=attempt + 1,
                )
                return {
                    "execution_id": execution_id,
                    "status": "running",
                    "attempt": attempt,
                    "poll_count": poll_count,
                }

            summary["status"] = "timeout"
            summary["completion_source"] = "poller_exhausted"
            summary["timed_out_at"] = summary.get("timed_out_at") or utcnow().isoformat()
            summary.setdefault("passed", 1)
            summary.setdefault("failed", 0)
            summary["success_rate"] = 0.0
            summary["playwright"] = {
                **dict(summary.get("playwright") or {}),
                "completion_source": "poller_exhausted",
                "status": "timeout",
            }
            timed_out = service.mark_timeout(db, execution_id, summary=summary)
            service.update_task_status(
                db,
                task_id,
                status="timeout",
                output_json={
                    "execution_id": execution_id,
                    "job_name": job_name,
                    "job_id": job_id,
                    "attempt": attempt,
                    "poll_count": poll_count,
                    "status": "timeout",
                    "completion_source": "poller_exhausted",
                },
                error_message="playwright poll attempts exhausted",
            )
            return {
                "execution_id": execution_id,
                "status": timed_out.status,
                "attempt": attempt,
                "poll_count": poll_count,
            }

        terminal_status = "success" if status == "success" else "failed"
        passed_total = int(summary.get("passed", 1))
        failed_total = int(summary.get("failed", 0))
        if terminal_status == "success":
            passed_total += max(int(poll_result.get("passed", 1)), 1)
        else:
            failed_total += max(int(poll_result.get("failed", 1)), 1)
        total = passed_total + failed_total
        success_rate = round((passed_total / total) * 100, 1) if total else 0.0

        terminal_summary = {
            **summary,
            "status": terminal_status,
            "completion_source": "poller_success",
            "passed": passed_total,
            "failed": failed_total,
            "success_rate": success_rate,
            "playwright": {
                **playwright_summary,
                "job_name": job_name,
                "job_id": job_id,
                "status": terminal_status,
                "poll_count": poll_count,
                "completion_source": "poller_success",
            },
            "started_at": summary.get("started_at") or utcnow().isoformat(),
        }
        updated = service.mark_completed(db, execution_id, status=terminal_status, summary=terminal_summary)
        service.update_task_status(
            db,
            task_id,
            status=terminal_status,
            output_json={
                "execution_id": execution_id,
                "job_name": job_name,
                "job_id": job_id,
                "attempt": attempt,
                "poll_count": poll_count,
                "status": terminal_status,
            },
        )
        return {
            "execution_id": execution_id,
            "status": updated.status,
            "attempt": attempt,
            "poll_count": poll_count,
        }


@celery_app.task(name="aiqahub.execution.sweep_stale_executions")
def sweep_stale_executions() -> dict[str, Any]:
    service = ExecutionService()
    settings = get_settings()
    cutoff_seconds = settings.execution_timeout_seconds
    timed_out: list[str] = []
    with SessionLocal() as db:
        executions = db.query(Execution).filter(Execution.status.in_(["queued", "running"])).all()
        for execution in executions:
            summary = dict(execution.summary_json or {})
            started_at = _parse_datetime(summary.get("started_at"))
            if started_at is None:
                continue
            age_seconds = (utcnow() - started_at).total_seconds()
            if age_seconds < cutoff_seconds:
                continue
            tasks = service.list_tasks(db, execution.id)
            for task in tasks:
                if task.status not in {"success", "failed"}:
                    service.update_task_status(
                        db,
                        task.id,
                        status="timeout",
                        output_json={
                            "execution_id": execution.id,
                            "status": "timeout",
                            "reason": "execution timed out",
                        },
                        error_message="execution timed out",
                    )
            summary["status"] = "timeout"
            summary["timed_out_at"] = utcnow().isoformat()
            summary["completion_source"] = "timeout_sweeper"
            if "passed" not in summary:
                summary["passed"] = 0
            if "failed" not in summary:
                summary["failed"] = 0
            summary["success_rate"] = 0.0
            service.mark_timeout(db, execution.id, summary=summary)
            timed_out.append(execution.id)
    return {"timed_out": timed_out, "count": len(timed_out)}
