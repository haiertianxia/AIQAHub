from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.execution import Execution
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


def test_suite_and_environment_update_delete_and_validation_hardening():
    token = uuid4().hex[:8]

    other_project = client.post(
        "/api/v1/projects",
        json={"code": f"p_{token}", "name": f"Project {token}"},
    )
    assert other_project.status_code == 200
    other_project_id = other_project.json()["id"]

    env_other = client.post(
        "/api/v1/environments",
        json={
            "project_id": other_project_id,
            "name": f"Env {token}",
            "env_type": "sit",
            "base_url": "https://example.invalid",
        },
    )
    assert env_other.status_code == 200
    env_other_id = env_other.json()["id"]

    suite_created = client.post(
        "/api/v1/suites",
        json={
            "project_id": "proj_demo",
            "name": f"Suite {token}",
            "suite_type": "api",
            "source_type": "local",
            "source_ref": f"ref:{token}",
            "default_env_id": None,
        },
    )
    assert suite_created.status_code == 200
    suite_id = suite_created.json()["id"]

    # Cross-project default_env_id should be rejected on update.
    suite_cross_update = client.put(
        f"/api/v1/suites/{suite_id}",
        json={
            "project_id": "proj_demo",
            "name": f"Suite {token}",
            "suite_type": "api",
            "source_type": "local",
            "source_ref": f"ref:{token}",
            "default_env_id": env_other_id,
        },
    )
    assert suite_cross_update.status_code == 400

    # Create a valid environment for proj_demo and set it as default.
    env_demo = client.post(
        "/api/v1/environments",
        json={
            "project_id": "proj_demo",
            "name": f"Env {token} demo",
            "env_type": "sit",
            "base_url": "https://demo.example.invalid",
        },
    )
    assert env_demo.status_code == 200
    env_demo_id = env_demo.json()["id"]

    suite_update = client.put(
        f"/api/v1/suites/{suite_id}",
        json={
            "project_id": "proj_demo",
            "name": f"Suite {token} updated",
            "suite_type": "api",
            "source_type": "local",
            "source_ref": f"ref:{token}:updated",
            "default_env_id": env_demo_id,
        },
    )
    assert suite_update.status_code == 200
    assert suite_update.json()["default_env_id"] == env_demo_id

    suite_project_update = client.put(
        f"/api/v1/suites/{suite_id}",
        json={
            "project_id": other_project_id,
            "name": f"Suite {token} updated again",
            "suite_type": "api",
            "source_type": "local",
            "source_ref": f"ref:{token}:project-hop",
            "default_env_id": None,
        },
    )
    assert suite_project_update.status_code == 400

    # Environment base_url must be HTTP(S).
    env_bad_url = client.post(
        "/api/v1/environments",
        json={
            "project_id": "proj_demo",
            "name": f"Env {token} bad",
            "env_type": "sit",
            "base_url": "ftp://example.invalid",
        },
    )
    assert env_bad_url.status_code == 400

    env_project_update = client.put(
        f"/api/v1/environments/{env_demo_id}",
        json={
            "project_id": other_project_id,
            "name": f"Env {token} demo",
            "env_type": "sit",
            "base_url": "https://demo.example.invalid",
        },
    )
    assert env_project_update.status_code == 400

    env_update_bad_url = client.put(
        f"/api/v1/environments/{env_demo_id}",
        json={
            "project_id": "proj_demo",
            "name": f"Env {token} demo",
            "env_type": "sit",
            "base_url": "not-a-url",
        },
    )
    assert env_update_bad_url.status_code == 400

    # Deletion should be blocked when referenced by an execution.
    exe_id = f"exe_{token}"
    with SessionLocal() as db:
        db.add(
            Execution(
                id=exe_id,
                project_id="proj_demo",
                suite_id=suite_id,
                env_id=env_demo_id,
                trigger_type="manual",
                trigger_source=token,
                status="queued",
                request_params_json={},
                summary_json={},
            )
        )
        db.commit()

    suite_delete_blocked = client.delete(f"/api/v1/suites/{suite_id}")
    env_delete_blocked = client.delete(f"/api/v1/environments/{env_demo_id}")
    assert suite_delete_blocked.status_code == 400
    assert env_delete_blocked.status_code == 400

    # After removing the referencing execution, deletion should be allowed.
    with SessionLocal() as db:
        execution = db.get(Execution, exe_id)
        assert execution is not None
        db.delete(execution)
        db.commit()

    env_delete_still_blocked = client.delete(f"/api/v1/environments/{env_demo_id}")
    assert env_delete_still_blocked.status_code == 400

    suite_delete = client.delete(f"/api/v1/suites/{suite_id}")
    env_delete = client.delete(f"/api/v1/environments/{env_demo_id}")
    assert suite_delete.status_code == 200
    assert env_delete.status_code == 200
