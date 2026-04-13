from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.ai_insight import AiInsight
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask


client = TestClient(app)


def test_reports_list_returns_seeded_execution_reports():
    response = client.get("/api/v1/reports")

    assert response.status_code == 200
    reports = response.json()
    assert reports, "expected at least one seeded report"
    assert reports[0]["execution_id"]
    assert "summary" in reports[0]
    assert "artifacts" in reports[0]


def test_reports_list_can_filter_by_search_and_completion_source():
    execution_id = "exe_report_filter"
    with SessionLocal() as db:
        db.add(
            Execution(
                id=execution_id,
                project_id="proj_demo",
                suite_id="suite_demo",
                env_id="env_demo",
                trigger_type="manual",
                trigger_source="ui",
                status="timeout",
                request_params_json={},
                summary_json={
                    "status": "timeout",
                    "completion_source": "timeout_sweeper",
                    "started_at": "2026-04-09T00:00:00Z",
                },
            )
        )
        db.commit()

    search_response = client.get("/api/v1/reports", params={"search": execution_id})
    source_response = client.get("/api/v1/reports", params={"completion_source": "timeout_sweeper"})

    assert search_response.status_code == 200
    assert source_response.status_code == 200
    assert any(item["execution_id"] == execution_id for item in search_response.json())
    assert any(item["execution_id"] == execution_id for item in source_response.json())

    with SessionLocal() as db:
        execution = db.get(Execution, execution_id)
        if execution is not None:
            db.delete(execution)
        db.commit()


def test_report_detail_is_available_for_seeded_execution():
    execution_id = "exe_demo"

    response = client.get(f"/api/v1/reports/{execution_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["execution_id"] == execution_id
    assert "artifacts" in payload
    assert "tasks" in payload


def test_reports_and_audit_exports_return_csv():
    report_response = client.get("/api/v1/reports/export")
    audit_response = client.get("/api/v1/audit/export")

    assert report_response.status_code == 200
    assert audit_response.status_code == 200
    assert report_response.headers["content-type"].startswith("text/csv")
    assert audit_response.headers["content-type"].startswith("text/csv")
    assert "execution_id" in report_response.text
    assert "action" in audit_response.text


def test_gate_rules_can_be_created_and_listed():
    create_response = client.post(
        "/api/v1/gates/rules",
        json={
            "project_id": "proj_seed",
            "name": "关键路径成功率",
            "rule_type": "success_rate",
            "enabled": True,
            "config": {"min_success_rate": 95},
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["name"] == "关键路径成功率"
    assert created["project_id"] == "proj_seed"

    list_response = client.get("/api/v1/gates/rules")
    assert list_response.status_code == 200
    rules = list_response.json()
    assert any(rule["id"] == created["id"] for rule in rules)


def test_gate_evaluation_uses_seeded_execution():
    executions = client.get("/api/v1/executions").json()
    execution_id = executions[0]["id"]

    response = client.post("/api/v1/gates/evaluate", json={"execution_id": execution_id})

    assert response.status_code == 200
    result = response.json()
    assert result["execution_id"] == execution_id
    assert result["result"] in {"PASS", "WARN", "FAIL"}


def test_execution_detail_exposes_timeline_and_artifacts():
    execution_id = client.get("/api/v1/executions").json()[0]["id"]

    artifacts_response = client.get(f"/api/v1/executions/{execution_id}/artifacts")
    timeline_response = client.get(f"/api/v1/executions/{execution_id}/timeline")

    assert artifacts_response.status_code == 200
    assert timeline_response.status_code == 200
    assert isinstance(artifacts_response.json(), list)
    assert isinstance(timeline_response.json(), list)


def test_execution_detail_exposes_completion_source():
    execution_id = client.get("/api/v1/executions").json()[0]["id"]
    response = client.get(f"/api/v1/executions/{execution_id}")

    assert response.status_code == 200
    payload = response.json()
    assert "completion_source" in payload
    assert "started_at" in payload


def test_gate_evaluation_uses_task_count_signal():
    create_rule_response = client.post(
        "/api/v1/gates/rules",
        json={
            "project_id": "proj_demo",
            "name": "任务数门禁",
            "rule_type": "task_count",
            "enabled": True,
            "config": {"min_task_count": 3, "min_success_rate": 95},
        },
    )
    assert create_rule_response.status_code == 200
    rule_id = create_rule_response.json()["id"]

    execution_id = f"exe_gate_task_count_{uuid4().hex[:8]}"
    with SessionLocal() as db:
        db.add(
            Execution(
                id=execution_id,
                project_id="proj_demo",
                suite_id="suite_demo",
                env_id="env_demo",
                trigger_type="manual",
                trigger_source="ui",
                status="success",
                request_params_json={},
                summary_json={"passed": 2, "failed": 0, "success_rate": 100.0},
            )
        )
        for index, task_key in enumerate(["prepare", "execute"], start=1):
            db.add(
                ExecutionTask(
                    id=f"task_gate_{uuid4().hex[:8]}",
                    execution_id=execution_id,
                    task_key=task_key,
                    task_name=task_key.title(),
                    task_order=index,
                    status="success",
                    input_json={},
                    output_json={},
                    error_message=None,
                )
            )
        db.commit()

    response = client.post("/api/v1/gates/evaluate", json={"execution_id": execution_id})

    assert response.status_code == 200
    body = response.json()
    assert body["task_count"] == 2
    assert body["result"] == "WARN"

    with SessionLocal() as db:
        for task in db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all():
            db.delete(task)
        execution = db.get(Execution, execution_id)
        if execution is not None:
            db.delete(execution)
        db.commit()
    client.delete(f"/api/v1/gates/rules/{rule_id}")


def test_gate_evaluation_fails_timeout_executions():
    execution_id = "exe_timeout_gate"
    with SessionLocal() as db:
        db.add(
            Execution(
                id=execution_id,
                project_id="proj_demo",
                suite_id="suite_demo",
                env_id="env_demo",
                trigger_type="manual",
                trigger_source="ui",
                status="timeout",
                request_params_json={},
                summary_json={
                    "status": "timeout",
                    "completion_source": "timeout_sweeper",
                    "started_at": "2026-04-09T00:00:00Z",
                },
            )
        )
        db.add(
            ExecutionTask(
                id="task_timeout_gate",
                execution_id=execution_id,
                task_key="collect",
                task_name="Collect",
                task_order=1,
                status="timeout",
                input_json={},
                output_json={},
                error_message="execution timed out",
            )
        )
        db.commit()

    response = client.post("/api/v1/gates/evaluate", json={"execution_id": execution_id})

    assert response.status_code == 200
    body = response.json()
    assert body["result"] == "FAIL"
    assert body["completion_source"] == "timeout_sweeper"

    with SessionLocal() as db:
        for task in db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all():
            db.delete(task)
        execution = db.get(Execution, execution_id)
        if execution is not None:
            db.delete(execution)
        db.commit()


def test_audit_logs_can_filter_by_search_and_action():
    with SessionLocal() as db:
        db.add(
            AuditLog(
                id="audit_filter_1",
                actor_id="user_a",
                action="create_execution",
                target_type="execution",
                target_id="exe_a",
                request_json={},
                response_json={},
            )
        )
        db.add(
            AuditLog(
                id="audit_filter_2",
                actor_id="user_b",
                action="delete_quality_rule",
                target_type="quality_rule",
                target_id="rule_b",
                request_json={},
                response_json={},
            )
        )
        db.commit()

    search_response = client.get("/api/v1/audit", params={"search": "delete_quality_rule"})
    action_response = client.get("/api/v1/audit", params={"action": "create_execution"})

    assert search_response.status_code == 200
    assert action_response.status_code == 200
    assert any(item["id"] == "audit_filter_2" for item in search_response.json())
    assert any(item["id"] == "audit_filter_1" for item in action_response.json())

    with SessionLocal() as db:
        for log_id in ["audit_filter_1", "audit_filter_2"]:
            log = db.get(AuditLog, log_id)
            if log is not None:
                db.delete(log)
        db.commit()


def test_ai_history_lists_recent_analysis():
    executions = client.get("/api/v1/executions").json()
    execution_id = executions[0]["id"]

    response = client.post(
        "/api/v1/ai/analyze",
        json={"input_text": "登录失败回归", "context": {"execution_id": execution_id}},
    )
    assert response.status_code == 200

    history_response = client.get("/api/v1/ai/history", params={"limit": 10})
    assert history_response.status_code == 200
    history = history_response.json()
    assert any(item["execution_id"] == execution_id for item in history)

    with SessionLocal() as db:
        for insight in db.query(AiInsight).filter(AiInsight.execution_id == execution_id).all():
            db.delete(insight)
        db.commit()


def test_ai_history_can_filter_by_execution_model_type_and_search():
    suffix = uuid4().hex[:8]
    execution_alpha = f"exe_history_alpha_{suffix}"
    execution_beta = f"exe_history_beta_{suffix}"
    insight_alpha = f"ai_history_filter_1_{suffix}"
    insight_beta = f"ai_history_filter_2_{suffix}"
    model_alpha = f"mock-llm-{suffix}"
    model_beta = f"other-llm-{suffix}"
    type_alpha = f"analysis-{suffix}"
    type_beta = f"summary-{suffix}"
    search_term = f"支付异常{suffix}"

    try:
        with SessionLocal() as db:
            db.add(
                AiInsight(
                    id=insight_alpha,
                    execution_id=execution_alpha,
                    insight_type=type_alpha,
                    model_name=model_alpha,
                    prompt_version="v1",
                    confidence=0.81,
                    input_json={
                        "input_text": "登录失败排查",
                        "context": {"execution_id": execution_alpha},
                    },
                    output_json={"summary": "登录失败", "notes": "alpha"},
                )
            )
            db.add(
                AiInsight(
                    id=insight_beta,
                    execution_id=execution_beta,
                    insight_type=type_beta,
                    model_name=model_beta,
                    prompt_version="v2",
                    confidence=0.92,
                    input_json={
                        "input_text": f"{search_term}分析",
                        "context": {"execution_id": execution_beta},
                    },
                    output_json={"summary": search_term, "notes": "beta"},
                )
            )
            db.commit()

        execution_response = client.get("/api/v1/ai/history", params={"limit": 10, "execution_id": execution_alpha})
        model_response = client.get("/api/v1/ai/history", params={"limit": 10, "model_name": model_beta})
        type_response = client.get("/api/v1/ai/history", params={"limit": 10, "insight_type": type_beta})
        search_response = client.get("/api/v1/ai/history", params={"limit": 10, "search": search_term})

        assert execution_response.status_code == 200
        assert model_response.status_code == 200
        assert type_response.status_code == 200
        assert search_response.status_code == 200

        assert [item["id"] for item in execution_response.json()] == [insight_alpha]
        assert [item["id"] for item in model_response.json()] == [insight_beta]
        assert [item["id"] for item in type_response.json()] == [insight_beta]
        assert [item["id"] for item in search_response.json()] == [insight_beta]
    finally:
        with SessionLocal() as db:
            for insight_id in [insight_alpha, insight_beta]:
                insight = db.get(AiInsight, insight_id)
                if insight is not None:
                    db.delete(insight)
            db.commit()


def test_ai_history_can_filter_by_provider_name():
    suffix = uuid4().hex[:8]
    provider_alpha = f"provider-openai-{suffix}"
    provider_beta = f"provider-mock-{suffix}"
    openai_id = f"ai_history_provider_openai_{suffix}"
    mock_id = f"ai_history_provider_mock_{suffix}"

    try:
        with SessionLocal() as db:
            db.add(
                AiInsight(
                    id=openai_id,
                    execution_id=f"exe_provider_openai_{suffix}",
                    insight_type="analysis",
                    model_name="qa-openai",
                    prompt_version="v1",
                    confidence=0.98,
                    input_json={"input_text": "provider openai", "context": {"execution_id": f"exe_provider_openai_{suffix}"}},
                    output_json={"provider": provider_alpha, "model": "qa-openai", "summary": "openai result"},
                )
            )
            db.add(
                AiInsight(
                    id=mock_id,
                    execution_id=f"exe_provider_mock_{suffix}",
                    insight_type="analysis",
                    model_name="qa-mock",
                    prompt_version="v1",
                    confidence=0.88,
                    input_json={"input_text": "provider mock", "context": {"execution_id": f"exe_provider_mock_{suffix}"}},
                    output_json={"provider": provider_beta, "model": "qa-mock", "summary": "mock result"},
                )
            )
            db.commit()

        openai_response = client.get("/api/v1/ai/history", params={"limit": 10, "provider_name": provider_alpha})
        mock_response = client.get("/api/v1/ai/history", params={"limit": 10, "provider_name": provider_beta})

        assert openai_response.status_code == 200
        assert mock_response.status_code == 200
        assert [item["id"] for item in openai_response.json()] == [openai_id]
        assert [item["id"] for item in mock_response.json()] == [mock_id]
        assert openai_response.json()[0]["provider_name"] == provider_alpha
        assert mock_response.json()[0]["provider_name"] == provider_beta
    finally:
        with SessionLocal() as db:
            for insight_id in [openai_id, mock_id]:
                insight = db.get(AiInsight, insight_id)
                if insight is not None:
                    db.delete(insight)
            db.commit()


def test_ai_history_paginates_results():
    suffix = uuid4().hex[:8]
    insights = []
    model_name = f"page-llm-{suffix}"
    with SessionLocal() as db:
        for index in range(1, 4):
            insight_id = f"ai_history_page_{index}_{suffix}"
            insights.append(insight_id)
            db.add(
                AiInsight(
                    id=insight_id,
                    execution_id=f"exe_page_{index}_{suffix}",
                    insight_type="analysis",
                    model_name=model_name,
                    prompt_version="v1",
                    confidence=0.7 + index / 100,
                    input_json={"input_text": f"page {index}", "context": {"execution_id": f"exe_page_{index}_{suffix}"}},
                    output_json={"summary": f"page {index}"},
                )
            )
        db.commit()

    try:
        page_one = client.get("/api/v1/ai/history", params={"page": 1, "page_size": 2, "model_name": model_name})
        page_two = client.get("/api/v1/ai/history", params={"page": 2, "page_size": 2, "model_name": model_name})

        assert page_one.status_code == 200
        assert page_two.status_code == 200
        assert [item["id"] for item in page_one.json()] == insights[::-1][:2]
        assert [item["id"] for item in page_two.json()] == insights[::-1][2:4]
    finally:
        with SessionLocal() as db:
            for insight_id in insights:
                insight = db.get(AiInsight, insight_id)
                if insight is not None:
                    db.delete(insight)
            db.commit()
