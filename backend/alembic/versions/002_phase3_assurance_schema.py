"""Phase 3 Schema — AI Assurance, Invariants, Contracts, Security, Risk, Evidence & Change Proof

Revision ID: 002_phase3_assurance_schema
Revises: 001_initial_phase1_schema
Create Date: 2026-10-05 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_phase3_assurance_schema"
down_revision: Union[str, None] = "001_initial_phase1_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Change Intents
    op.create_table(
        "change_intents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("affected_capability", sa.String(length=255), nullable=False),
        sa.Column("expected_behavior", sa.Text(), nullable=True),
        sa.Column("affected_components", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.9"),
        sa.Column("model_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_change_intents_change_id", "change_intents", ["change_id"])
    op.create_index("ix_change_intents_analysis_run_id", "change_intents", ["analysis_run_id"])

    # 2. Behavioral Invariants
    op.create_table(
        "behavioral_invariants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invariant_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("affected_component", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("verification_status", sa.String(length=50), nullable=False, server_default="UNVERIFIED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_behavioral_invariants_change_id", "behavioral_invariants", ["change_id"])
    op.create_index("ix_behavioral_invariants_analysis_run_id", "behavioral_invariants", ["analysis_run_id"])

    # 3. Semantic Contracts
    op.create_table(
        "semantic_contracts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint_path", sa.String(length=255), nullable=False),
        sa.Column("http_method", sa.String(length=20), nullable=False),
        sa.Column("contract_type", sa.String(length=50), nullable=False),
        sa.Column("classification", sa.String(length=50), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_semantic_contracts_change_id", "semantic_contracts", ["change_id"])
    op.create_index("ix_semantic_contracts_analysis_run_id", "semantic_contracts", ["analysis_run_id"])

    # 4. Security Findings
    op.create_table(
        "security_findings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("affected_component", sa.String(length=255), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("remediation_suggestion", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.9"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_security_findings_change_id", "security_findings", ["change_id"])
    op.create_index("ix_security_findings_analysis_run_id", "security_findings", ["analysis_run_id"])

    # 5. Test Recommendations
    op.create_table(
        "test_recommendations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_component", sa.String(length=255), nullable=False),
        sa.Column("test_title", sa.String(length=255), nullable=False),
        sa.Column("test_code_scaffold", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("invariant_covered", sa.String(length=255), nullable=True),
        sa.Column("expected_behavior", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_test_recommendations_change_id", "test_recommendations", ["change_id"])
    op.create_index("ix_test_recommendations_analysis_run_id", "test_recommendations", ["analysis_run_id"])

    # 6. Risk Assessments
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_risk", sa.String(length=50), nullable=False),
        sa.Column("numerical_score", sa.Float(), nullable=False),
        sa.Column("contributing_factors", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.9"),
        sa.Column("uncertainties", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_assessments_change_id", "risk_assessments", ["change_id"])
    op.create_index("ix_risk_assessments_analysis_run_id", "risk_assessments", ["analysis_run_id"])

    # 7. Evidence Records
    op.create_table(
        "evidence_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_reference", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_records_analysis_run_id", "evidence_records", ["analysis_run_id"])

    # 8. Policy Decisions
    op.create_table(
        "policy_decisions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("rules_evaluated", sa.JSON(), nullable=False),
        sa.Column("blocking_reasons", sa.JSON(), nullable=True),
        sa.Column("warning_reasons", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_policy_decisions_change_id", "policy_decisions", ["change_id"])
    op.create_index("ix_policy_decisions_analysis_run_id", "policy_decisions", ["analysis_run_id"])

    # 9. Change Proofs
    op.create_table(
        "change_proofs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("change_id", sa.String(length=36), sa.ForeignKey("changes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("risk_level", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("full_proof_artifact", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("analysis_run_id", name="uq_change_proof_analysis_run"),
    )
    op.create_index("ix_change_proofs_change_id", "change_proofs", ["change_id"])
    op.create_index("ix_change_proofs_analysis_run_id", "change_proofs", ["analysis_run_id"])


def downgrade() -> None:
    op.drop_table("change_proofs")
    op.drop_table("policy_decisions")
    op.drop_table("evidence_records")
    op.drop_table("risk_assessments")
    op.drop_table("test_recommendations")
    op.drop_table("security_findings")
    op.drop_table("semantic_contracts")
    op.drop_table("behavioral_invariants")
    op.drop_table("change_intents")
