from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_assets_list_returns_seeded_asset():
    response = client.get("/api/v1/assets")

    assert response.status_code == 200
    assets = response.json()
    assert assets, "expected seeded assets"
    assert assets[0]["id"]
    assert assets[0]["asset_type"]


def test_assets_create_persists_new_asset():
    payload = {
        "project_id": "proj_demo",
        "asset_type": "prompt",
        "name": "Search Prompt",
        "version": "v2",
        "source_ref": "prompts/search",
        "metadata": {"owner": "qa"},
    }
    create_response = client.post("/api/v1/assets", json=payload)

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["name"] == payload["name"]
    assert created["version"] == payload["version"]
    assert created["metadata"] == payload["metadata"]

    list_response = client.get("/api/v1/assets")
    assert any(asset["name"] == payload["name"] for asset in list_response.json())
