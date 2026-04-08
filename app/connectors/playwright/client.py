from app.connectors.base import Connector


class PlaywrightConnector(Connector):
    def test_connection(self) -> dict:
        return {"ok": True, "type": "playwright"}

