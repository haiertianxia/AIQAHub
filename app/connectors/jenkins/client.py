from app.connectors.base import Connector
from app.core.config import get_settings


class JenkinsConnector(Connector):
    def __init__(self, base_url: str | None = None, username: str | None = None, token: str | None = None) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.jenkins_url
        self.username = username or settings.jenkins_user
        self.token = token or settings.jenkins_token


    def test_connection(self) -> dict:
        configured = bool(self.base_url and self.username)
        return {
            "ok": configured,
            "type": "jenkins",
            "message": "Jenkins connector configured" if configured else "Jenkins connector missing configuration",
            "base_url": self.base_url,
        }

    def trigger_job(self, job_name: str, parameters: dict | None = None) -> dict:
        return {
            "job_name": job_name,
            "build_number": 42,
            "queue_id": f"queue_{job_name}",
            "parameters": parameters or {},
            "url": f"{self.base_url.rstrip('/')}/job/{job_name}/42/" if self.base_url else f"job/{job_name}/42",
        }

    def get_build_status(self, job_name: str, build_number: int, *, final_status: str = "success") -> dict:
        return {
            "job_name": job_name,
            "build_number": build_number,
            "status": final_status.upper(),
            "result": final_status,
        }

    def list_artifacts(self, job_name: str, build_number: int) -> list[dict]:
        return [
            {
                "name": f"{job_name}-{build_number}-console.log",
                "type": "text/plain",
                "url": f"{self.base_url.rstrip('/')}/job/{job_name}/{build_number}/consoleText" if self.base_url else "",
            },
            {
                "name": f"{job_name}-{build_number}-archive.zip",
                "type": "application/zip",
                "url": f"{self.base_url.rstrip('/')}/job/{job_name}/{build_number}/artifact/archive.zip" if self.base_url else "",
            },
        ]
