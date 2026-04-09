from __future__ import annotations

import json
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask
from app.services.webhook_security import compute_jenkins_webhook_signature, replay_cache


client = TestClient(app)


def _seed_execution(execution_id: str) -> None:
    with SessionLocal() as db:
        db.add(
            Execution(
                id=execution_id,
                project_id="proj_seed",
                suite_id="suite_seed",
                env_id="env_seed",
                trigger_type="manual",
                trigger_source="ui",
                status="running",
                request_params_json={},
                summary_json={},
            )
        )
        for index, task_key in enumerate(["trigger_job", "wait_for_build"], start=1):
            db.add(
                ExecutionTask(
                    id=f"{execution_id}_{task_key}",
                    execution_id=execution_id,
                    task_key=task_key,
                    task_name=task_key.replace("_", " ").title(),
                    task_order=index,
                    status="running",
                    input_json={},
                    output_json={},
                    error_message=None,
                )
            )
        db.commit()


def _cleanup_execution(execution_id: str) -> None:
    with SessionLocal() as db:
        for task in db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all():
            db.delete(task)
        execution = db.get(Execution, execution_id)
        if execution is not None:
            db.delete(execution)
        db.commit()


def _build_headers(payload: dict[str, object], *, timestamp: int | None = None, nonce: str | None = None, signature: str | None = None) -> dict[str, str]:
    settings = get_settings()
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp_value = str(timestamp if timestamp is not None else int(time.time()))
    nonce_value = nonce or f"nonce_{uuid4().hex}"
    signature_value = signature or compute_jenkins_webhook_signature(
        secret=settings.jenkins_webhook_secret,
        timestamp=timestamp_value,
        nonce=nonce_value,
        execution_id=str(payload["execution_id"]),
        body=body,
    )
    return {
        "X-AIQA-Timestamp": timestamp_value,
        "X-AIQA-Nonce": nonce_value,
        "X-AIQA-Signature": signature_value,
        "X-AIQA-Execution-Id": str(payload["execution_id"]),
        "Content-Type": "application/json",
    }


def test_jenkins_callback_accepts_valid_hmac_signature():
    replay_cache.clear()
    execution_id = f"exe_webhook_{uuid4().hex[:8]}"
    _seed_execution(execution_id)

    payload = {
        "execution_id": execution_id,
        "job_name": "webchat-regression",
        "build_number": 42,
        "result": "SUCCESS",
        "build_url": "https://jenkins.example.com/job/webchat-regression/42/",
    }
    body = json.dumps(payload, separators=(",", ":"))

    response = client.post(
        "/api/v1/connectors/jenkins/callback",
        content=body.encode("utf-8"),
        headers=_build_headers(payload),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == execution_id
    assert data["status"] == "success"
    assert data["summary"]["jenkins"]["build_number"] == 42

    _cleanup_execution(execution_id)


def test_jenkins_callback_rejects_invalid_signature():
    replay_cache.clear()
    execution_id = f"exe_webhook_{uuid4().hex[:8]}"
    _seed_execution(execution_id)

    payload = {
        "execution_id": execution_id,
        "job_name": "webchat-regression",
        "build_number": 43,
        "result": "FAILED",
        "build_url": "https://jenkins.example.com/job/webchat-regression/43/",
    }
    body = json.dumps(payload, separators=(",", ":"))
    headers = _build_headers(payload, signature="deadbeef")

    response = client.post(
        "/api/v1/connectors/jenkins/callback",
        content=body.encode("utf-8"),
        headers=headers,
    )

    assert response.status_code == 400
    assert "invalid Jenkins webhook signature" in response.json()["detail"]

    _cleanup_execution(execution_id)


def test_jenkins_callback_rejects_replayed_nonce_and_expired_timestamp():
    replay_cache.clear()
    execution_id = f"exe_webhook_{uuid4().hex[:8]}"
    _seed_execution(execution_id)

    payload = {
        "execution_id": execution_id,
        "job_name": "webchat-regression",
        "build_number": 44,
        "result": "SUCCESS",
        "build_url": "https://jenkins.example.com/job/webchat-regression/44/",
    }
    body = json.dumps(payload, separators=(",", ":"))
    nonce = f"nonce_{uuid4().hex}"
    headers = _build_headers(payload, nonce=nonce)

    first_response = client.post(
        "/api/v1/connectors/jenkins/callback",
        content=body.encode("utf-8"),
        headers=headers,
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/connectors/jenkins/callback",
        content=body.encode("utf-8"),
        headers=headers,
    )
    assert second_response.status_code == 400
    assert "duplicate Jenkins webhook nonce" in second_response.json()["detail"]

    expired_headers = _build_headers(payload, timestamp=int(time.time()) - 600, nonce=f"nonce_{uuid4().hex}")
    expired_response = client.post(
        "/api/v1/connectors/jenkins/callback",
        content=body.encode("utf-8"),
        headers=expired_headers,
    )
    assert expired_response.status_code == 400
    assert "timestamp outside allowed window" in expired_response.json()["detail"]

    _cleanup_execution(execution_id)
