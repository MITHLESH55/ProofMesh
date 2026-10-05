"""
Pydantic schemas for Phase 5 Agent Governance, Tasks, Action Ledgers, Approvals, Remediation, and Change Proof v3.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Agent Definition Schemas ---

class AgentDefinitionCreate(BaseModel):
    organization_id: str
    name: str
    agent_type: str  # REVIEW_AGENT, TEST_AGENT, SECURITY_AGENT, ARCHITECTURE_AGENT, REMEDIATION_AGENT, ORCHESTRATOR_AGENT
    provider: str = "mock"
    model: str = "gemini-1.5-pro"
    version: str = "1.0.0"
    status: str = "ACTIVE"
    autonomy_level: int = 1
    owner_id: Optional[str] = None
    capabilities: List[str] = Field(default_factory=lambda: ["READ_REPOSITORY", "READ_GRAPH", "ANALYZE_DIFF"])
    allowed_scopes: Dict[str, Any] = Field(default_factory=lambda: {"repositories": ["*"], "services": ["*"]})


class AgentDefinitionResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    agent_type: str
    provider: str
    model: str
    version: str
    status: str
    autonomy_level: int
    owner_id: Optional[str] = None
    capabilities: List[str]
    allowed_scopes: Dict[str, Any]
    created_at: datetime


# --- Agent Task Schemas ---

class AgentTaskCreate(BaseModel):
    organization_id: str
    agent_id: str
    change_id: str
    analysis_run_id: str
    task_type: str = "MULTI_AGENT_ASSURANCE"
    initiator_type: str = "SYSTEM"
    initiator_id: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None


class AgentTaskResponse(BaseModel):
    id: str
    organization_id: str
    agent_id: str
    change_id: str
    analysis_run_id: str
    task_type: str
    status: str
    initiator_type: str
    initiator_id: Optional[str] = None
    plan: Dict[str, Any]
    result: Dict[str, Any]
    step_count: int
    token_count: int
    cost_estimate: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


# --- Agent Action Ledger Schemas ---

class AgentActionCreate(BaseModel):
    task_id: str
    agent_id: str
    organization_id: str
    repository_id: Optional[str] = None
    change_id: Optional[str] = None
    analysis_run_id: Optional[str] = None
    action_type: str
    requested_capability: str
    tool_name: str
    input_summary: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    policy_decision: str = "ALLOWED"
    status: str = "SUCCESS"


class AgentActionResponse(BaseModel):
    id: str
    task_id: str
    agent_id: str
    organization_id: str
    repository_id: Optional[str] = None
    change_id: Optional[str] = None
    analysis_run_id: Optional[str] = None
    action_type: str
    requested_capability: str
    tool_name: str
    input_summary: Dict[str, Any]
    output_summary: Dict[str, Any]
    policy_decision: str
    status: str
    created_at: datetime


# --- Agent Approval Schemas ---

class AgentApprovalRequest(BaseModel):
    organization_id: str
    task_id: Optional[str] = None
    change_id: str
    requesting_agent_id: str
    requested_action: str
    risk_level: str = "HIGH"
    affected_resources: List[str] = Field(default_factory=list)
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)


class AgentApprovalDecision(BaseModel):
    decision: str  # APPROVED, REJECTED
    reason: Optional[str] = None


class AgentApprovalResponse(BaseModel):
    id: str
    organization_id: str
    task_id: Optional[str] = None
    change_id: str
    requesting_agent_id: str
    requested_action: str
    risk_level: str
    affected_resources: List[str]
    evidence_summary: Dict[str, Any]
    status: str
    approver_user_id: Optional[str] = None
    decision_reason: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime


# --- Remediation Proposal Schemas ---

class RemediationProposalCreate(BaseModel):
    organization_id: str
    change_id: str
    agent_id: str
    title: str
    description: str
    original_risk_score: float
    original_risk_level: str
    proposed_diff: str
    explanation: str
    affected_components: List[str] = Field(default_factory=list)


class RemediationProposalResponse(BaseModel):
    id: str
    organization_id: str
    change_id: str
    agent_id: str
    title: str
    description: str
    original_risk_score: float
    original_risk_level: str
    proposed_diff: str
    explanation: str
    affected_components: List[str]
    verified_risk_score: float
    verified_risk_level: str
    verification_status: str
    verification_evidence: Dict[str, Any]
    approval_id: Optional[str] = None
    created_at: datetime


# --- Change Proof v3 Schemas ---

class ChangeProofV3Response(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    version: str
    overall_verdict: str
    risk_level: str
    risk_score: float
    proof_document: Dict[str, Any]
    created_at: datetime
