from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_connectors_includes_jenkins():
    response = client.get("/api/v1/connectors")

    assert response.status_code == 200
    connectors = response.json()
    assert any(connector["connector_type"] == "jenkins" for connector in connectors)


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
