from app.connectors.base import Connector


class PlaywrightConnector(Connector):
    def validate_config(self) -> dict:
        return {"ok": True, "type": "playwright"}
