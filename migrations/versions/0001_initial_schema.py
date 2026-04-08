"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-08 00:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_roles_code", "roles", ["code"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
    )
    op.create_index("ix_projects_code", "projects", ["code"], unique=True)

    op.create_table(
        "test_suites",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("suite_type", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=False),
        sa.Column("default_env_id", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_test_suites_project_id", "test_suites", ["project_id"])

    op.create_table(
        "environments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("env_type", sa.String(length=32), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("credential_ref", sa.Text(), nullable=True),
        sa.Column("db_ref", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_environments_project_id", "environments", ["project_id"])

    op.create_table(
        "executions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("suite_id", sa.String(length=64), nullable=False),
        sa.Column("env_id", sa.String(length=64), nullable=False),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("trigger_source", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="created"),
        sa.Column("request_params_json", sa.JSON(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_executions_project_id", "executions", ["project_id"])
    op.create_index("ix_executions_suite_id", "executions", ["suite_id"])
    op.create_index("ix_executions_env_id", "executions", ["env_id"])

    op.create_table(
        "execution_artifacts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("execution_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
    )
    op.create_index("ix_execution_artifacts_execution_id", "execution_artifacts", ["execution_id"])

    op.create_table(
        "quality_rules",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("rule_type", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_quality_rules_project_id", "quality_rules", ["project_id"])

    op.create_table(
        "ai_insights",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("execution_id", sa.String(length=64), nullable=False),
        sa.Column("insight_type", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("input_json", sa.JSON(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=True),
    )
    op.create_index("ix_ai_insights_execution_id", "ai_insights", ["execution_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("request_json", sa.JSON(), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_index("ix_ai_insights_execution_id", table_name="ai_insights")
    op.drop_table("ai_insights")
    op.drop_index("ix_quality_rules_project_id", table_name="quality_rules")
    op.drop_table("quality_rules")
    op.drop_index("ix_execution_artifacts_execution_id", table_name="execution_artifacts")
    op.drop_table("execution_artifacts")
    op.drop_index("ix_executions_env_id", table_name="executions")
    op.drop_index("ix_executions_suite_id", table_name="executions")
    op.drop_index("ix_executions_project_id", table_name="executions")
    op.drop_table("executions")
    op.drop_index("ix_environments_project_id", table_name="environments")
    op.drop_table("environments")
    op.drop_index("ix_test_suites_project_id", table_name="test_suites")
    op.drop_table("test_suites")
    op.drop_index("ix_projects_code", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_roles_code", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

