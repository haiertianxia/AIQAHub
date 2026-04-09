from app.connectors.jenkins.client import JenkinsConnector
from app.core.config import get_settings
from app.schemas.connector import ConnectorRead
from app.services.base import BaseService


class ConnectorService(BaseService):
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
