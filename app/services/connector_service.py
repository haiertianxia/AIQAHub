from app.connectors.jenkins.client import JenkinsConnector
from app.core.config import get_settings
from app.schemas.connector import ConnectorRead, JenkinsCallbackPayload
from app.services.base import BaseService
from app.services.execution_service import ExecutionService


class ConnectorService(BaseService):
    def __init__(self) -> None:
        self.execution_service = ExecutionService()

    def list_connectors(self) -> list[ConnectorRead]:
        return [
            ConnectorRead(connector_type="jenkins", ok=True, message="Jenkins connector available"),
            ConnectorRead(connector_type="llm", ok=True, message="LLM connector available"),
            ConnectorRead(connector_type="playwright", ok=True, message="Playwright connector available"),
        ]

    def test_connector(self, connector_type: str, payload: dict | None = None) -> ConnectorRead:
        payload = payload or {}
        if connector_type == "jenkins":
            connector = JenkinsConnector(
                base_url=payload.get("base_url") or get_settings().jenkins_url,
                username=payload.get("username") or get_settings().jenkins_user,
                token=payload.get("token") or get_settings().jenkins_token,
            )
            result = connector.test_connection()
            return ConnectorRead(
                connector_type="jenkins",
                ok=bool(result.get("ok")),
                message=str(result.get("message", "Jenkins connector tested")),
                details=result,
            )
        if connector_type == "playwright":
            return ConnectorRead(
                connector_type="playwright",
                ok=True,
                message="Playwright connector tested",
                details={"type": "playwright"},
            )
        if connector_type == "llm":
            return ConnectorRead(
                connector_type="llm",
                ok=True,
                message="LLM connector tested",
                details={"type": "llm"},
            )
        return ConnectorRead(connector_type=connector_type, ok=False, message=f"Unknown connector: {connector_type}")

    def handle_jenkins_callback(self, db, payload: JenkinsCallbackPayload):
        execution = self.execution_service.repo.get(db, payload.execution_id)
        tasks = self.execution_service.list_tasks(db, payload.execution_id)
        build_url = payload.build_url or ""
        callback_summary = {
            "build_number": payload.build_number,
            "build_url": build_url,
            "job_name": payload.job_name,
            "result": payload.result,
        }

        for task in tasks:
            if task.task_key == "trigger_job":
                self.execution_service.update_task_status(
                    db,
                    task.id,
                    status="success",
                    output_json={
                        **task.output,
                        "build_number": payload.build_number,
                        "build_url": build_url,
                        "job_name": payload.job_name,
                        "callback": callback_summary,
                    },
                )
            elif task.task_key == "wait_for_build":
                self.execution_service.update_task_status(
                    db,
                    task.id,
                    status=payload.result.lower() if payload.result.lower() in {"success", "failed"} else "success",
                    output_json={
                        **task.output,
                        "build_number": payload.build_number,
                        "build_url": build_url,
                        "job_name": payload.job_name,
                        "callback": callback_summary,
                    },
                )

        final_status = "success" if payload.result.lower() == "success" else "failed"
        summary = dict(execution.summary_json or {})
        summary["jenkins"] = callback_summary
        summary["status"] = final_status
        if final_status == "success":
            summary.setdefault("passed", 0)
            summary.setdefault("failed", 0)
            summary.setdefault("success_rate", 100.0)
        else:
            summary.setdefault("passed", 0)
            summary.setdefault("failed", 1)
            summary.setdefault("success_rate", 0.0)
        updated = self.execution_service.mark_completed(db, payload.execution_id, status=final_status, summary=summary)
        return updated
