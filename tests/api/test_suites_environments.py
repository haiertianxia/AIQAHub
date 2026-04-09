from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_suites_and_environments_support_project_filtering_and_detail():
    suites_response = client.get("/api/v1/suites?project_id=proj_demo")
    env_response = client.get("/api/v1/environments?project_id=proj_demo")

    assert suites_response.status_code == 200
    assert env_response.status_code == 200

    suites = suites_response.json()
    environments = env_response.json()
    assert suites, "expected seeded suites"
    assert environments, "expected seeded environments"
    assert all(item["project_id"] == "proj_demo" for item in suites)
    assert all(item["project_id"] == "proj_demo" for item in environments)

    suite_detail = client.get(f"/api/v1/suites/{suites[0]['id']}")
    env_detail = client.get(f"/api/v1/environments/{environments[0]['id']}")

    assert suite_detail.status_code == 200
    assert env_detail.status_code == 200
    assert suite_detail.json()["id"] == suites[0]["id"]
    assert env_detail.json()["id"] == environments[0]["id"]
