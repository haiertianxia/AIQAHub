from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.execution import Execution
from app.models.execution_task import ExecutionTask


client = TestClient(app)


def test_report_summary_includes_task_details():
    execution_id = f"exe_{uuid4().hex[:12]}"
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
        db.add(
            ExecutionTask(
                id=f"task_{uuid4().hex[:12]}",
                execution_id=execution_id,
                task_key="prepare",
                task_name="Prepare Context",
                task_order=1,
                status="success",
                input_json={"phase": "prepare"},
                output_json={"status": "success"},
                error_message=None,
            )
        )
        db.commit()

    response = client.get(f"/api/v1/reports/{execution_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["task_count"] == 1
    assert body["tasks"][0]["task_key"] == "prepare"
    assert body["tasks"][0]["status"] == "success"

    with SessionLocal() as db:
        for task in db.query(ExecutionTask).filter(ExecutionTask.execution_id == execution_id).all():
            db.delete(task)
        execution = db.get(Execution, execution_id)
        if execution is not None:
            db.delete(execution)
        db.commit()
