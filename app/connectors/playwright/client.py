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

    def trigger_job(self, job_name: str, parameters: dict | None = None) -> dict:
        runtime = {k: v for k, v in (parameters or {}).items() if k in self.runtime_override_fields}
        browser = str(runtime.get("browser") or self.default_browser or "chromium")
        headless_value = runtime.get("headless")
        headless = self.default_headless if headless_value is None else bool(headless_value)
        base_url = str(runtime.get("base_url") or self.default_base_url)
        return {
            "job_name": job_name,
            "job_id": f"playwright-{job_name}",
            "status": self.normalize_status("queued"),
            "command": self.command,
            "workdir": self.workdir,
            "browser": browser,
            "headless": headless,
            "base_url": base_url,
            "runtime": runtime,
            "type": "playwright",
        }
