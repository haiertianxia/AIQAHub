from app.connectors.base import Connector
from app.schemas.connector import ConnectorResult


class LLMConnector(Connector):
    def validate_config(self) -> dict:
        return ConnectorResult(
            connector_type="llm",
            ok=True,
            status="success",
            message="LLM connector configured",
            details={"type": "llm"},
        ).model_dump()
