from app.connectors.base import Connector
from app.schemas.connector import ConnectorResult


class PlaywrightConnector(Connector):
    def validate_config(self) -> dict:
        return ConnectorResult(
            connector_type="playwright",
            ok=True,
            status="success",
            message="Playwright connector configured",
            details={"type": "playwright"},
        ).model_dump()
