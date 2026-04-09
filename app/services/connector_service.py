from collections.abc import Mapping

from app.connectors.jenkins.client import JenkinsConnector
from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.schemas.connector import ConnectorRead, JenkinsCallbackPayload
from app.services.base import BaseService
from app.services.execution_service import ExecutionService
from app.services.webhook_security import verify_jenkins_webhook


class ConnectorService(BaseService):
    def __init__(self) -> None:
        self.execution_service = ExecutionService()

    @staticmethod
    def _normalise_jenkins_payload(value: object) -> dict[str, object]:
        return dict(value) if isinstance(value, dict) else {}

    @staticmethod
    def _build_jenkins_summary(
        *,
        execution_summary: dict[str, object] | None,
        callback_summary: dict[str, object],
        final_status: str,
        completion_source: str,
    ) -> dict[str, object]:
        summary = dict(execution_summary or {})
        summary["jenkins"] = {**ConnectorService._normalise_jenkins_payload(summary.get("jenkins")), **callback_summary}
        summary["jenkins"]["completion_source"] = completion_source
        summary["status"] = final_status
        if final_status == "success":
            summary.setdefault("passed", 0)
            summary.setdefault("failed", 0)
            summary.setdefault("success_rate", 100.0)
        elif final_status == "failed":
            summary.setdefault("passed", 0)
            summary.setdefault("failed", 1)
            summary.setdefault("success_rate", 0.0)
        return summary

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

    def _apply_jenkins_result(
        self,
        db,
        payload: JenkinsCallbackPayload,
    ):
        execution = self.execution_service.repo.get(db, payload.execution_id)
        current_status = (execution.status or "created").lower()
        if current_status in {"success", "failed", "cancelled", "timeout"}:
            return self.execution_service._to_read(execution)

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
        summary = self._build_jenkins_summary(
            execution_summary=execution.summary_json,
            callback_summary=callback_summary,
            final_status=final_status,
            completion_source="callback",
        )
        updated = self.execution_service.mark_completed(db, payload.execution_id, status=final_status, summary=summary)
        return updated

    def handle_jenkins_callback(
        self,
        db,
        payload: JenkinsCallbackPayload,
        *,
        headers: Mapping[str, str] | None = None,
        raw_body: bytes | None = None,
    ):
        verify_jenkins_webhook(
            secret=get_settings().jenkins_webhook_secret,
            headers=headers or {},
            body=raw_body or b"",
            max_skew_seconds=get_settings().jenkins_webhook_tolerance_seconds,
        )
        return self._apply_jenkins_result(db, payload)

    def poll_jenkins_build(self, db, payload: JenkinsCallbackPayload):
        connector = JenkinsConnector()
        execution = self.execution_service.repo.get(db, payload.execution_id)
        request_params = dict(execution.request_params_json or {})
        summary = dict(execution.summary_json or {})
        jenkins_summary = self._normalise_jenkins_payload(summary.get("jenkins"))
        sequence = request_params.get("jenkins_poll_sequence")
        if isinstance(sequence, list) and sequence:
            normalized_sequence = [str(item).lower() for item in sequence if str(item).strip()]
        else:
            normalized_sequence = ["success"]
        poll_count = int(jenkins_summary.get("poll_count", 0))
        sequence_index = min(poll_count, len(normalized_sequence) - 1)
        desired_result = normalized_sequence[sequence_index]
        status_payload = connector.get_build_status(
            payload.job_name,
            payload.build_number,
            final_status=desired_result if desired_result in {"success", "failed"} else "running",
        )
        result = str(status_payload.get("result") or "running").lower()
        if result not in {"success", "failed"}:
            jenkins_summary["poll_count"] = poll_count + 1
            jenkins_summary["job_name"] = payload.job_name
            jenkins_summary["build_number"] = payload.build_number
            jenkins_summary["build_url"] = payload.build_url or ""
            jenkins_summary["queue_id"] = jenkins_summary.get("queue_id")
            jenkins_summary["poll_status"] = status_payload.get("status", "RUNNING")
            summary["jenkins"] = jenkins_summary
            summary["status"] = "running"
            summary["completion_source"] = "poller"
            if "started_at" not in summary:
                summary["started_at"] = summary.get("started_at") or summary.get("created_at")
            updated = self.execution_service.update_summary(db, payload.execution_id, summary)
            if poll_count + 1 < get_settings().jenkins_poll_attempts:
                return updated
            return updated

        return self._apply_jenkins_result(
            db,
            JenkinsCallbackPayload(
                execution_id=payload.execution_id,
                job_name=payload.job_name,
                build_number=payload.build_number,
                result=result,
                build_url=payload.build_url,
            ),
        )
