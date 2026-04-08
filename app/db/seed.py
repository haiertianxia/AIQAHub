from sqlalchemy.orm import Session

from app.models.artifact import ExecutionArtifact
from app.models.environment import Environment
from app.models.audit_log import AuditLog
from app.models.execution import Execution
from app.models.project import Project
from app.models.quality_rule import QualityRule
from app.models.suite import TestSuite


def seed_demo_data(db: Session) -> None:
    project = db.get(Project, "proj_demo")
    if project is None:
        project = Project(
            id="proj_demo",
            code="omnichannel",
            name="Omnichannel",
            description="企业全渠道客服系统",
            owner_id="user_demo",
        )
        db.add(project)

    suite = db.get(TestSuite, "suite_demo")
    if suite is None:
        suite = TestSuite(
            id="suite_demo",
            project_id="proj_demo",
            name="API 回归套件",
            suite_type="api",
            source_type="jenkins",
            source_ref="job/webchat-gateway-regression",
            default_env_id="env_demo",
        )
        db.add(suite)

    env = db.get(Environment, "env_demo")
    if env is None:
        env = Environment(
            id="env_demo",
            project_id="proj_demo",
            name="SIT",
            env_type="sit",
            base_url="https://sit.example.com",
            enabled=True,
        )
        db.add(env)

    execution = db.get(Execution, "exe_demo")
    if execution is None:
        execution = Execution(
            id="exe_demo",
            project_id="proj_demo",
            suite_id="suite_demo",
            env_id="env_demo",
            trigger_type="manual",
            trigger_source="ui",
            status="success",
            request_params_json={"branch": "main"},
            summary_json={"total": 120, "passed": 116, "failed": 4, "success_rate": 96.7},
        )
        db.add(execution)

    artifact = db.get(ExecutionArtifact, "art_demo")
    if artifact is None:
        artifact = ExecutionArtifact(
            id="art_demo",
            execution_id="exe_demo",
            artifact_type="allure",
            name="allure-report",
            storage_uri="s3://reports/exe_demo/allure",
        )
        db.add(artifact)

    rule = db.get(QualityRule, "rule_demo")
    if rule is None:
        rule = QualityRule(
            id="rule_demo",
            project_id="proj_demo",
            name="成功率门禁",
            rule_type="success_rate",
            enabled=True,
            config_json={"threshold": 95},
        )
        db.add(rule)

    audit = db.get(AuditLog, "audit_demo")
    if audit is None:
        audit = AuditLog(
            id="audit_demo",
            actor_id="user_demo",
            action="seed_demo_data",
            target_type="system",
            target_id="proj_demo",
            request_json={"seed": True},
            response_json={"status": "ok"},
            note="Initial demo data",
        )
        db.add(audit)

    db.commit()
