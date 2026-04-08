from app.connectors.base import Connector


class LLMConnector(Connector):
    def test_connection(self) -> dict:
        return {"ok": True, "type": "llm"}

