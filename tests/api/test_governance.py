from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask
from app.main import app
from app.services.audit_service import AuditService
from app.services.settings_service import SettingsService
from app.schemas.settings import SettingsUpdate

client = TestClient(app)


def _insert_failed_execution(execution_id: str) -> None:
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    with SessionLocal() as db:
        db.add(
            Execution(
                id=execution_id,
                project_id="proj_demo",
                suite_id="suite_demo",
                env_id="env_demo",
                trigger_type="manual",
                trigger_source="ui",
                status="failed",
                request_params_json={"stage": "sit"},
                summary_json={
                    "status": "failed",
                    "completion_source": "callback",
                    "completed_at": now,
                    "failed": 1,
                },
            )
        )
        db.add(
            ExecutionTask(
                id=f"task_{uuid4().hex[:8]}",
                execution_id=execution_id,
                task_key="execute",
                task_name="Execute",
                task_order=1,
                status="failed",
                input_json={},
                output_json={},
                error_message="simulated failure",
            )
        )
        db.commit()


def _insert_audit_event(audit_id: str) -> None:
    with SessionLocal() as db:
        db.add(
            AuditLog(
                id=audit_id,
                actor_id="user_demo",
                action="governance_test_event",
                target_type="system",
                target_id="proj_demo",
                request_json={"seed": "governance"},
                response_json={"status": "ok"},
                note="governance test",
            )
        )
        db.commit()


def test_governance_overview_returns_recent_counts():
    execution_id = f"exe_gov_{uuid4().hex[:8]}"
    audit_id = f"audit_gov_{uuid4().hex[:8]}"
    environment = f"gov_{uuid4().hex[:6]}"

    _insert_failed_execution(execution_id)
    _insert_audit_event(audit_id)
    SettingsService().update_settings(
        payload=SettingsUpdate(app_name="AIQAHub-Governance"),
        environment=environment,
    )

    service = AuditService()
    with SessionLocal() as db:
        overview = service.get_governance_overview(db)

    assert overview.window == "last_24h"
    assert overview.recent_audit_count >= 1
    assert overview.gate_fail_count >= 1
    assert overview.settings_rollback_count >= 0
    assert overview.asset_block_count >= 0
    assert isinstance(overview.recent_events, list)


def test_governance_events_have_stable_ids():
    service = AuditService()
    with SessionLocal() as db:
        first = service.list_governance_events(db)
        second = service.list_governance_events(db)

    first_map = {(event.kind, event.source_type, event.source_id): event.id for event in first}
    second_map = {(event.kind, event.source_type, event.source_id): event.id for event in second}

    assert first_map
    assert first_map == second_map
    for event in first:
        assert event.timestamp.endswith("Z")


def test_governance_event_detail_matches_event_stream():
    service = AuditService()
    with SessionLocal() as db:
        events = service.list_governance_events(db)
        assert events
        event = events[0]
        detail = service.get_governance_event_detail(db, event.id)

    assert detail is not None
    assert detail.id == event.id
    assert detail.kind == event.kind
    assert detail.source_type == event.source_type
    assert detail.source_id == event.source_id


def test_governance_overview_endpoint_returns_last_24h_window():
    response = client.get("/api/v1/governance/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["window"] == "last_24h"
    assert payload["window_start"].endswith("Z")
    assert payload["window_end"].endswith("Z")
    assert isinstance(payload["recent_events"], list)


def test_governance_events_endpoint_filters_by_type():
    response = client.get("/api/v1/governance/events?kind=audit_event&limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert len(payload) <= 5
    assert {item["kind"] for item in payload} == {"audit_event"}


def test_governance_event_detail_endpoint_matches_event_stream():
    events_response = client.get("/api/v1/governance/events?limit=1")
    assert events_response.status_code == 200
    events = events_response.json()
    assert events

    detail_response = client.get(f"/api/v1/governance/events/{events[0]['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()

    assert detail["id"] == events[0]["id"]
    assert detail["kind"] == events[0]["kind"]
    assert detail["source_type"] == events[0]["source_type"]
    assert detail["source_id"] == events[0]["source_id"]
