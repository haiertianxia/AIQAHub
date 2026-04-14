import shlex
import shutil
from pathlib import Path

from app.core.config import get_settings
from app.connectors.base import Connector
from app.schemas.connector import ConnectorResult


class PlaywrightConnector(Connector):
    runtime_override_fields = {"base_url", "browser", "headless", "suite_name", "report_mode"}

    def __init__(
        self,
        *,
        enabled: bool | None = None,
        command: str | None = None,
        workdir: str | None = None,
        default_base_url: str | None = None,
        default_browser: str | None = None,
        default_headless: bool | None = None,
    ) -> None:
        settings = get_settings()
        self.enabled = settings.playwright_enabled if enabled is None else enabled
        self.command = (settings.playwright_command if command is None else command).strip()
        self.workdir = (settings.playwright_workdir if workdir is None else workdir).strip()
        self.default_base_url = (
            settings.playwright_default_base_url if default_base_url is None else default_base_url
        ).strip()
        self.default_browser = (settings.playwright_default_browser if default_browser is None else default_browser).strip()
        self.default_headless = settings.playwright_default_headless if default_headless is None else default_headless

    def validate_config(self) -> dict:
        if not self.enabled:
            return ConnectorResult(
                connector_type="playwright",
                ok=False,
                status="failed",
                message="Playwright connector is disabled by configuration",
                details={"enabled": self.enabled},
            ).model_dump()

        missing = []
        if not self.command:
            missing.append("playwright_command")
        if not self.workdir:
            missing.append("playwright_workdir")
        if missing:
            return ConnectorResult(
                connector_type="playwright",
                ok=False,
                status="failed",
                message="Playwright connector missing required configuration",
                details={"missing": missing},
            ).model_dump()

        workdir_path = Path(self.workdir)
        if not workdir_path.exists() or not workdir_path.is_dir():
            return ConnectorResult(
                connector_type="playwright",
                ok=False,
                status="failed",
                message="Playwright connector workdir is not available",
                details={"workdir": self.workdir},
            ).model_dump()

        command_parts = shlex.split(self.command)
        executable = command_parts[0] if command_parts else ""
        executable_path = shutil.which(executable) if executable else None
        if not executable_path:
            return ConnectorResult(
                connector_type="playwright",
                ok=False,
                status="failed",
                message="Playwright connector command is not runnable",
                details={"command": self.command, "executable": executable},
            ).model_dump()

        return ConnectorResult(
            connector_type="playwright",
            ok=True,
            status="success",
            message="Playwright connector configured",
            details={
                "enabled": self.enabled,
                "command": self.command,
                "workdir": self.workdir,
                "default_base_url": self.default_base_url,
                "default_browser": self.default_browser,
                "default_headless": self.default_headless,
            },
        ).model_dump()

    @staticmethod
    def _coerce_int(value: object, default: int) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default

    def _build_artifact_uris(self, job_id: str, parameters: dict | None = None) -> dict[str, str]:
        report_root = str((parameters or {}).get("report_root") or f"memory://playwright/{job_id}")
        artifacts = {
            "playwright-junit": f"{report_root}/junit.xml",
            "playwright-html-report": f"{report_root}/html-report/index.html",
        }
        if bool((parameters or {}).get("include_trace")):
            artifacts["playwright-trace"] = f"{report_root}/trace.zip"
        if bool((parameters or {}).get("include_screenshot")):
            artifacts["playwright-screenshot"] = f"{report_root}/screenshot.png"
        if bool((parameters or {}).get("include_video")):
            artifacts["playwright-video"] = f"{report_root}/video.webm"
        return artifacts

    def trigger_playwright(self, job_name: str, parameters: dict | None = None) -> dict:
        runtime = {k: v for k, v in (parameters or {}).items() if k in self.runtime_override_fields}
        browser = str(runtime.get("browser") or self.default_browser or "chromium")
        headless_value = runtime.get("headless")
        headless = self.default_headless if headless_value is None else bool(headless_value)
        base_url = str(runtime.get("base_url") or self.default_base_url)
        job_id = f"playwright-{job_name}"
        return {
            "job_name": job_name,
            "job_id": job_id,
            "status": self.normalize_status("queued"),
            "command": self.command,
            "workdir": self.workdir,
            "browser": browser,
            "headless": headless,
            "base_url": base_url,
            "runtime": runtime,
            "artifacts": self._build_artifact_uris(job_id, parameters),
            "type": "playwright",
        }

    def wait_for_playwright(self, job_name: str, job_id: str, *, parameters: dict | None = None, poll_count: int = 0) -> dict:
        sequence = (parameters or {}).get("playwright_poll_sequence")
        if isinstance(sequence, list) and sequence:
            normalized_sequence = [str(item).lower() for item in sequence if str(item).strip()]
        else:
            normalized_sequence = ["success"]
        sequence_index = min(poll_count, len(normalized_sequence) - 1)
        status = self.normalize_status(normalized_sequence[sequence_index], default="running")
        passed_default = 1 if status == "success" else 0
        failed_default = 1 if status == "failed" else 0
        return {
            "job_name": job_name,
            "job_id": job_id,
            "status": status,
            "poll_count": poll_count + 1,
            "passed": self._coerce_int((parameters or {}).get("playwright_passed"), passed_default),
            "failed": self._coerce_int((parameters or {}).get("playwright_failed"), failed_default),
            "artifacts": self._build_artifact_uris(job_id, parameters),
        }

    def trigger_job(self, job_name: str, parameters: dict | None = None) -> dict:
        return self.trigger_playwright(job_name, parameters)
