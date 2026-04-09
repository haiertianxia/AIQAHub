from app.connectors.base import Connector


class LLMConnector(Connector):
    def validate_config(self) -> dict:
        return {"ok": True, "type": "llm"}
