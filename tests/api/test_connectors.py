from fastapi.testclient import TestClient

from app.connectors.jenkins.client import JenkinsConnector
from app.main import app


client = TestClient(app)


def test_list_connectors_includes_jenkins():
    response = client.get("/api/v1/connectors")

    assert response.status_code == 200
    connectors = response.json()
    assert any(connector["connector_type"] == "jenkins" and connector["status"] == "success" for connector in connectors)


def test_test_jenkins_connector_returns_status():
    response = client.post(
        "/api/v1/connectors/jenkins/test",
        json={
            "payload": {
                "base_url": "https://jenkins.example.com",
                "username": "demo",
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["connector_type"] == "jenkins"
    assert body["ok"] is True
    assert body["status"] == "success"


def test_jenkins_connector_normalizes_execution_statuses():
    connector = JenkinsConnector(base_url="https://jenkins.example.com", username="demo")

    trigger = connector.trigger_job("webchat-regression")
    running = connector.get_build_status("webchat-regression", 42, final_status="RUNNING")
    success = connector.get_build_status("webchat-regression", 42, final_status="SUCCESS")

    assert trigger["status"] == "queued"
    assert running["status"] == "running"
    assert success["status"] == "success"
