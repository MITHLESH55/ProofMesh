"""Phase 5 Schema — Enterprise Intelligence, Teams, Services, Ownership, Cross-Repo Dependencies, Agents, Governance, Approvals, Remediation, Change Proof v3.

Revision ID: 004_phase5_enterprise_schema
Revises: 003_phase4_runtime_schema
Create Date: 2026-10-05 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_phase5_enterprise_schema"
down_revision: Union[str, None] = "003_phase4_runtime_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Teams
    op.create_table(
        "teams",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_teams_organization_id", "teams", ["organization_id"])

    # 2. Services
    op.create_table(
        "services",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", sa.String(length=36), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("repository_id", sa.String(length=36), sa.ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("criticality", sa.String(length=50), nullable=False, server_default="MEDIUM"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_services_organization_id", "services", ["organization_id"])
    op.create_index("ix_services_team_id", "services", ["team_id"])
    op.create_index("ix_services_name", "services", ["name"])

    # 3. Component Ownerships
    op.create_table(
        "component_ownerships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("service_id", sa.String(length=36), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=True),
        sa.Column("repository_id", sa.String(length=36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("component_path", sa.String(length=255), nullable=False),
        sa.Column("owner_team_id", sa.String(length=36), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("owner_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="EXPLICIT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_component_ownerships_repository_id", "component_ownerships", ["repository_id"])

    # 4. Cross Repo Dependencies
    op.create_table(
        "cross_repo_dependencies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_repository_id", sa.String(length=36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_repository_id", sa.String(length=36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dependency_type", sa.String(length=50), nullable=False),
        sa.Column("package_or_service_name", sa.String(length=100), nullable=False),
        sa.Column("provenance_details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cross_repo_deps_org", "cross_repo_dependencies", ["organization_id"])

    # 5. Enterprise Graph Versions
    op.create_table(
        "enterprise_graph_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_tag", sa.String(length=100), nullable=False),
        sa.Column("commit_sha", sa.String(length=64), nullable=False),
        sa.Column("graph_snapshot_ref", sa.String(length=255), nullable=True),
        sa.Column("node_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("edge_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 6. Historical Evidence
    op.create_table(
        "historical_evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repository_id", sa.String(length=36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_historical_evidence_org", "historical_evidence", ["organization_id"])

    # 7. Incident Records
    op.create_table(
        "incident_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", sa.String(length=36), sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="HIGH"),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("regression_metric", sa.String(length=100), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Agent Definitions
    op.create_table(
        "agent_definitions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="mock"),
        sa.Column("model", sa.String(length=100), nullable=False, server_default="gemini-1.5-pro"),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("autonomy_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("allowed_scopes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_definitions_org", "agent_definitions", ["organization_id"])

    # 9. Agent Tasks
    op.create_table(
        "agent_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(length=36), sa.ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("initiator_type", sa.String(length=50), nullable=False, server_default="SYSTEM"),
        sa.Column("initiator_id", sa.String(length=36), nullable=True),
        sa.Column("plan", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("step_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_estimate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_tasks_change_id", "agent_tasks", ["change_id"])

    # 10. Agent Actions Ledger
    op.create_table(
        "agent_actions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(length=36), sa.ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repository_id", sa.String(length=36), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("requested_capability", sa.String(length=50), nullable=False),
        sa.Column("tool_name", sa.String(length=50), nullable=False),
        sa.Column("input_summary", sa.JSON(), nullable=False),
        sa.Column("output_summary", sa.JSON(), nullable=False),
        sa.Column("policy_decision", sa.String(length=50), nullable=False, server_default="ALLOWED"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SUCCESS"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_actions_task_id", "agent_actions", ["task_id"])

    # 11. Agent Approvals
    op.create_table(
        "agent_approvals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requesting_agent_id", sa.String(length=36), sa.ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_action", sa.String(length=100), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False, server_default="HIGH"),
        sa.Column("affected_resources", sa.JSON(), nullable=False),
        sa.Column("evidence_summary", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("approver_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_approvals_change_id", "agent_approvals", ["change_id"])

    # 12. Remediation Proposals
    op.create_table(
        "remediation_proposals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(length=36), sa.ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("original_risk_score", sa.Float(), nullable=False),
        sa.Column("original_risk_level", sa.String(length=50), nullable=False),
        sa.Column("proposed_diff", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("affected_components", sa.JSON(), nullable=False),
        sa.Column("verified_risk_score", sa.Float(), nullable=False),
        sa.Column("verified_risk_level", sa.String(length=50), nullable=False),
        sa.Column("verification_status", sa.String(length=50), nullable=False, server_default="VERIFIED_SAFER"),
        sa.Column("verification_evidence", sa.JSON(), nullable=False),
        sa.Column("approval_id", sa.String(length=36), sa.ForeignKey("agent_approvals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_remediation_proposals_change_id", "remediation_proposals", ["change_id"])

    # 13. Change Proofs v3
    op.create_table(
        "change_proofs_v3",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="3.0.0"),
        sa.Column("overall_verdict", sa.String(length=50), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("proof_document", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_change_proofs_v3_change_id", "change_proofs_v3", ["change_id"])


def downgrade() -> None:
    op.drop_table("change_proofs_v3")
    op.drop_table("remediation_proposals")
    op.drop_table("agent_approvals")
    op.drop_table("agent_actions")
    op.drop_table("agent_tasks")
    op.drop_table("agent_definitions")
    op.drop_table("incident_records")
    op.drop_table("historical_evidence")
    op.drop_table("enterprise_graph_versions")
    op.drop_table("cross_repo_dependencies")
    op.drop_table("component_ownerships")
    op.drop_table("services")
    op.drop_table("teams")
