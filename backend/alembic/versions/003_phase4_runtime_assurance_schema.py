"""Phase 4 Schema — Deployments, Runtime Telemetry, Observations, Baselines, Findings & CI Gates

Revision ID: 003_phase4_runtime_assurance_schema
Revises: 002_phase3_assurance_schema
Create Date: 2026-10-05 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_phase4_runtime_assurance_schema"
down_revision: Union[str, None] = "002_phase3_assurance_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Deployments
    op.create_table(
        "deployments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("repository_id", sa.String(length=36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=False),
        sa.Column("environment", sa.String(length=50), nullable=False, server_default="staging"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DEPLOYED"),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_deployments_repository_id", "deployments", ["repository_id"])
    op.create_index("ix_deployments_change_id", "deployments", ["change_id"])
    op.create_index("ix_deployments_analysis_run_id", "deployments", ["analysis_run_id"])
    op.create_index("ix_deployments_commit_sha", "deployments", ["commit_sha"])

    # 2. Runtime Baselines
    op.create_table(
        "runtime_baselines",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("deployment_id", sa.String(length=36), sa.ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False, server_default="*"),
        sa.Column("request_rate", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("error_rate", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("p50_latency_ms", sa.Float(), nullable=False, server_default="45.0"),
        sa.Column("p95_latency_ms", sa.Float(), nullable=False, server_default="120.0"),
        sa.Column("p99_latency_ms", sa.Float(), nullable=False, server_default="220.0"),
        sa.Column("sample_window_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runtime_baselines_deployment_id", "runtime_baselines", ["deployment_id"])
    op.create_index("ix_runtime_baselines_service_name", "runtime_baselines", ["service_name"])

    # 3. Runtime Observations
    op.create_table(
        "runtime_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("deployment_id", sa.String(length=36), sa.ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False, server_default="*"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("p50_latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("p95_latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("p99_latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status_2xx_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status_4xx_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status_5xx_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runtime_observations_deployment_id", "runtime_observations", ["deployment_id"])
    op.create_index("ix_runtime_observations_service_name", "runtime_observations", ["service_name"])

    # 4. Runtime Findings
    op.create_table(
        "runtime_findings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("deployment_id", sa.String(length=36), sa.ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("finding_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="LOW"),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("endpoint_or_metric", sa.String(length=255), nullable=False),
        sa.Column("baseline_value", sa.Float(), nullable=True),
        sa.Column("observed_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runtime_findings_deployment_id", "runtime_findings", ["deployment_id"])

    # 5. CI Assurance Checks
    op.create_table(
        "ci_assurance_checks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=False),
        sa.Column("gate_decision", sa.String(length=50), nullable=False),
        sa.Column("policy_summary", sa.JSON(), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("github_check_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ci_assurance_checks_change_id", "ci_assurance_checks", ["change_id"])
    op.create_index("ix_ci_assurance_checks_commit_sha", "ci_assurance_checks", ["commit_sha"])


def downgrade() -> None:
    op.drop_table("ci_assurance_checks")
    op.drop_table("runtime_findings")
    op.drop_table("runtime_observations")
    op.drop_table("runtime_baselines")
    op.drop_table("deployments")
