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


def test_assets_create_writes_initial_revision():
    payload = {
        "project_id": "proj_demo",
        "asset_type": "prompt",
        "name": "Revision Prompt",
        "version": "v1",
        "source_ref": "prompts/revision",
        "metadata": {"owner": "qa"},
    }
    create_response = client.post("/api/v1/assets", json=payload)

    assert create_response.status_code == 200
    asset_id = create_response.json()["id"]

    revisions_response = client.get(f"/api/v1/assets/{asset_id}/revisions")

    assert revisions_response.status_code == 200
    revisions = revisions_response.json()
    assert len(revisions) == 1
    assert revisions[0]["revision_number"] == 1
    assert revisions[0]["version"] == payload["version"]
    assert revisions[0]["snapshot"]["name"] == payload["name"]


def test_assets_update_writes_new_revision():
    payload = {
        "project_id": "proj_demo",
        "asset_type": "prompt",
        "name": "Update Prompt",
        "version": "v1",
        "source_ref": "prompts/update",
        "metadata": {"owner": "qa"},
    }
    create_response = client.post("/api/v1/assets", json=payload)
    asset_id = create_response.json()["id"]

    updated_payload = {
        **payload,
        "name": "Update Prompt v2",
        "version": "v2",
        "metadata": {"owner": "qa", "tag": "updated"},
    }
    update_response = client.put(f"/api/v1/assets/{asset_id}", json=updated_payload)

    assert update_response.status_code == 200
    assert update_response.json()["name"] == updated_payload["name"]

    revisions_response = client.get(f"/api/v1/assets/{asset_id}/revisions")
    revisions = revisions_response.json()

    assert len(revisions) == 2
    assert [revision["revision_number"] for revision in revisions] == [1, 2]
    assert revisions[-1]["snapshot"]["name"] == updated_payload["name"]
    assert revisions[-1]["snapshot"]["metadata"] == updated_payload["metadata"]


def test_assets_revision_history_is_ordered():
    payload = {
        "project_id": "proj_demo",
        "asset_type": "prompt",
        "name": "Ordered Prompt",
        "version": "v1",
        "source_ref": "prompts/ordered",
        "metadata": {"owner": "qa"},
    }
    create_response = client.post("/api/v1/assets", json=payload)
    asset_id = create_response.json()["id"]

    for index in range(2, 5):
        client.put(
            f"/api/v1/assets/{asset_id}",
            json={
                **payload,
                "name": f"Ordered Prompt v{index}",
                "version": f"v{index}",
                "metadata": {"owner": "qa", "revision": index},
            },
        )

    revisions_response = client.get(f"/api/v1/assets/{asset_id}/revisions")
    revisions = revisions_response.json()

    assert [revision["revision_number"] for revision in revisions] == [1, 2, 3, 4]
    assert revisions[0]["snapshot"]["name"] == payload["name"]
    assert revisions[-1]["snapshot"]["name"] == "Ordered Prompt v4"
