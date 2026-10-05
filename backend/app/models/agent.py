"""
Phase 5 Agent Domain Models — Agent Identity, Governance, Tasks, Action Ledger, Approvals, Remediation, Change Proof v3.
"""
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentDefinition(Base):
    """First-class identity and configuration for AI & autonomous coding agents."""
    __tablename__ = "agent_definitions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)  # REVIEW_AGENT, TEST_AGENT, SECURITY_AGENT, ARCHITECTURE_AGENT, REMEDIATION_AGENT, ORCHESTRATOR_AGENT
    provider = Column(String(50), nullable=False, default="mock")  # openai, anthropic, google, mock
    model = Column(String(100), nullable=False, default="gemini-1.5-pro")
    version = Column(String(50), nullable=False, default="1.0.0")
    status = Column(String(50), nullable=False, default="ACTIVE")  # ACTIVE, DISABLED, RESTRICTED
    autonomy_level = Column(Integer, nullable=False, default=1)  # 0: Observe, 1: Analyze, 2: Generate Artifacts, 3: Create PRs, 4: Operational, 5: Autonomous
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    capabilities = Column(JSON, nullable=False, default=list)  # ["READ_REPOSITORY", "READ_GRAPH", "GENERATE_TESTS", "PROPOSE_PATCH"]
    allowed_scopes = Column(JSON, nullable=False, default=dict)  # {"repositories": ["*"], "services": ["*"]}
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    tasks = relationship("AgentTask", back_populates="agent", cascade="all, delete-orphan")
    actions = relationship("AgentAction", back_populates="agent", cascade="all, delete-orphan")


class AgentTask(Base):
    """Orchestrated execution unit of work performed by an agent."""
    __tablename__ = "agent_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)  # MULTI_AGENT_ASSURANCE, SECURITY_DEEP_DIVE, REMEDIATION_PLAN, TEST_SYNTHESIS
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, BUDGET_EXCEEDED
    initiator_type = Column(String(50), nullable=False, default="SYSTEM")  # HUMAN, SYSTEM, AGENT
    initiator_id = Column(String(36), nullable=True)
    plan = Column(JSON, nullable=False, default=dict)
    result = Column(JSON, nullable=False, default=dict)
    step_count = Column(Integer, nullable=False, default=0)
    token_count = Column(Integer, nullable=False, default=0)
    cost_estimate = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    agent = relationship("AgentDefinition", back_populates="tasks")
    actions = relationship("AgentAction", back_populates="task", cascade="all, delete-orphan")


class AgentAction(Base):
    """Immutable audit ledger of every tool and operational action taken by an agent."""
    __tablename__ = "agent_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, index=True)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=True, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    action_type = Column(String(50), nullable=False)  # READ_FILE, QUERY_GRAPH, QUERY_RUNTIME, RUN_TESTS, GENERATE_TEST, PROPOSE_REMEDIATION, CREATE_BRANCH, CREATE_PR
    requested_capability = Column(String(50), nullable=False)
    tool_name = Column(String(50), nullable=False)
    input_summary = Column(JSON, nullable=False, default=dict)
    output_summary = Column(JSON, nullable=False, default=dict)
    policy_decision = Column(String(50), nullable=False, default="ALLOWED")  # ALLOWED, BLOCKED, PENDING_APPROVAL
    status = Column(String(50), nullable=False, default="SUCCESS")  # SUCCESS, FAILED, BLOCKED
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    agent = relationship("AgentDefinition", back_populates="actions")
    task = relationship("AgentTask", back_populates="actions")


class AgentApproval(Base):
    """Human-in-the-loop approval gate for agent actions and autonomous remediation."""
    __tablename__ = "agent_approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    requesting_agent_id = Column(String(36), ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False)
    requested_action = Column(String(100), nullable=False)  # e.g., "CREATE_PULL_REQUEST", "APPLY_REMEDIATION_PATCH"
    risk_level = Column(String(50), nullable=False, default="HIGH")
    affected_resources = Column(JSON, nullable=False, default=list)
    evidence_summary = Column(JSON, nullable=False, default=dict)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, APPROVED, REJECTED, EXPIRED
    approver_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision_reason = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class RemediationProposal(Base):
    """Formal patch proposal generated by a Remediation Agent with before/after risk verification."""
    __tablename__ = "remediation_proposals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agent_definitions.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    original_risk_score = Column(Float, nullable=False)
    original_risk_level = Column(String(50), nullable=False)
    proposed_diff = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    affected_components = Column(JSON, nullable=False, default=list)
    verified_risk_score = Column(Float, nullable=False)
    verified_risk_level = Column(String(50), nullable=False)
    verification_status = Column(String(50), nullable=False, default="VERIFIED_SAFER")  # PENDING, VERIFIED_SAFER, REJECTED_REGRESSION, FAILED_VERIFICATION
    verification_evidence = Column(JSON, nullable=False, default=dict)
    approval_id = Column(String(36), ForeignKey("agent_approvals.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class ChangeProofV3(Base):
    """Canonical Phase 5 Enterprise Change Proof unifying static, dynamic, historical, and agentic assurance."""
    __tablename__ = "change_proofs_v3"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(50), nullable=False, default="3.0.0")
    overall_verdict = Column(String(50), nullable=False)  # VERIFIED_SAFE, BLOCKED, RUNTIME_REGRESSION, REMEDIATION_PENDING_APPROVAL, REMEDIATION_VERIFIED
    risk_level = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    proof_document = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
