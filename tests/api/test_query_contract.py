import csv
from io import StringIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.ai_insight import AiInsight
from app.models.audit_log import AuditLog
from app.models.execution import Execution
from app.main import app


client = TestClient(app)


def _csv_rows(response) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(response.text))
    return list(reader)


def test_shared_search_and_pagination_across_list_endpoints():
    token = f"query-contract-{uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/executions",
        json={
            "project_id": "proj_demo",
            "suite_id": "suite_demo",
            "env_id": "env_demo",
            "trigger_type": "manual",
            "trigger_source": token,
            "request_params": {"search_token": token},
        },
    )
    assert created.status_code == 200

    executions = client.get(f"/api/v1/executions?search={token}&page=1&page_size=1")
    reports = client.get(f"/api/v1/reports?search={token}&page=1&page_size=1")
    audit = client.get(f"/api/v1/audit?search={token}&page=1&page_size=1")

    ai_response = client.post(
        "/api/v1/ai/analyze",
        json={"input_text": f"{token} query for unified search", "context": {"execution_id": "exe_demo", "token": token}},
    )
    assert ai_response.status_code == 200
    ai_history = client.get(f"/api/v1/ai/history?search={token}&page=1&page_size=1")

    for response in (executions, reports, audit, ai_history):
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1

    assert executions.json()[0]["trigger_source"] == token
    assert reports.json()[0]["completion_source"] in {None, "trigger"}
    assert audit.json()[0]["action"] == "create_execution"
    assert ai_history.json()[0]["execution_id"] == "exe_demo"


def test_report_and_audit_exports_use_the_same_filters_as_list_endpoints():
    token = f"query-contract-export-{uuid4().hex[:8]}"
    created = client.post(
        "/api/v1/executions",
        json={
            "project_id": "proj_demo",
            "suite_id": "suite_demo",
            "env_id": "env_demo",
            "trigger_type": "manual",
            "trigger_source": token,
            "request_params": {"export_token": token},
        },
    )
    assert created.status_code == 200

    report_list = client.get(f"/api/v1/reports?search={token}")
    report_export = client.get(f"/api/v1/reports/export?search={token}")
    audit_list = client.get(f"/api/v1/audit?search={token}")
    audit_export = client.get(f"/api/v1/audit/export?search={token}")

    assert report_list.status_code == 200
    assert report_export.status_code == 200
    assert audit_list.status_code == 200
    assert audit_export.status_code == 200

    report_rows = _csv_rows(report_export)
    audit_rows = _csv_rows(audit_export)

    assert report_rows and report_rows[0]["execution_id"] == report_list.json()[0]["execution_id"]
    assert audit_rows and audit_rows[0]["id"] == audit_list.json()[0]["id"]


def test_execution_search_uses_shared_query_contract():
    response = client.get("/api/v1/executions?search=exe_demo&page=1&page_size=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert any(item["id"] == "exe_demo" for item in payload)


def test_sort_param_is_shared_across_list_endpoints():
    token = f"query-contract-sort-{uuid4().hex[:8]}"
    execution_success_id = f"exe_{token}_success"
    execution_failed_id = f"exe_{token}_failed"
    audit_alpha_id = f"audit_{token}_alpha"
    audit_zeta_id = f"audit_{token}_zeta"
    insight_alpha_id = f"ai_{token}_alpha"
    insight_zeta_id = f"ai_{token}_zeta"

    with SessionLocal() as db:
        db.add(
            Execution(
                id=execution_success_id,
                project_id="proj_demo",
                suite_id="suite_demo",
                env_id="env_demo",
                trigger_type="manual",
                trigger_source=token,
                status="success",
                request_params_json={},
                summary_json={"completion_source": "trigger"},
            )
        )
        db.add(
            Execution(
                id=execution_failed_id,
                project_id="proj_demo",
                suite_id="suite_demo",
                env_id="env_demo",
                trigger_type="manual",
                trigger_source=token,
                status="failed",
                request_params_json={},
                summary_json={"completion_source": "callback"},
            )
        )
        db.add(
            AuditLog(
                id=audit_zeta_id,
                actor_id="user_demo",
                action=f"{token}_zeta",
                target_type="execution",
                target_id=execution_success_id,
                request_json={},
                response_json={},
            )
        )
        db.add(
            AuditLog(
                id=audit_alpha_id,
                actor_id="user_demo",
                action=f"{token}_alpha",
                target_type="execution",
                target_id=execution_failed_id,
                request_json={},
                response_json={},
            )
        )
        db.add(
            AiInsight(
                id=insight_zeta_id,
                execution_id=execution_success_id,
                insight_type="analysis",
                model_name=f"{token}_zeta_model",
                prompt_version="v1",
                confidence=0.5,
                input_json={"input_text": token},
                output_json={"summary": token},
            )
        )
        db.add(
            AiInsight(
                id=insight_alpha_id,
                execution_id=execution_failed_id,
                insight_type="analysis",
                model_name=f"{token}_alpha_model",
                prompt_version="v1",
                confidence=0.6,
                input_json={"input_text": token},
                output_json={"summary": token},
            )
        )
        db.commit()

    try:
        executions = client.get(
            f"/api/v1/executions?search={token}&sort=status&page=1&page_size=2"
        )
        reports = client.get(
            f"/api/v1/reports?search={token}&sort=status&page=1&page_size=2"
        )
        audit = client.get(
            f"/api/v1/audit?search={token}&sort=action&page=1&page_size=2"
        )
        ai_history = client.get(
            f"/api/v1/ai/history?search={token}&sort=model_name&page=1&page_size=2"
        )

        assert executions.status_code == 200
        assert reports.status_code == 200
        assert audit.status_code == 200
        assert ai_history.status_code == 200

        execution_items = executions.json()
        report_items = reports.json()
        audit_items = audit.json()
        history_items = ai_history.json()

        assert execution_items[0]["id"] == execution_failed_id
        assert report_items[0]["execution_id"] == execution_failed_id
        assert audit_items[0]["id"] == audit_alpha_id
        assert history_items[0]["id"] == insight_alpha_id
    finally:
        with SessionLocal() as db:
            for insight_id in [insight_alpha_id, insight_zeta_id]:
                insight = db.get(AiInsight, insight_id)
                if insight is not None:
                    db.delete(insight)
            for audit_id in [audit_alpha_id, audit_zeta_id]:
                log = db.get(AuditLog, audit_id)
                if log is not None:
                    db.delete(log)
            for execution_id in [execution_success_id, execution_failed_id]:
                execution = db.get(Execution, execution_id)
                if execution is not None:
                    db.delete(execution)
            db.commit()
