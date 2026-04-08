from app.connectors.base import Connector


class JenkinsConnector(Connector):
    def test_connection(self) -> dict:
        return {"ok": True, "type": "jenkins"}

