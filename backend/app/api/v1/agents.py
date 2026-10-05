"""
Phase 5 Agent Governance API Endpoints.

Provides endpoints for:
- Agent identity registration and management
- Capability policy checks
- Task orchestration and lifecycle management
- Immutable action audit ledger
- Human-in-the-loop approval gates
- Remediation proposal creation and verification
- Change Proof v3 assembly
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, NotFoundError
from app.core.logging import logger
from app.db.session import get_db
from app.models.entities import User
from app.schemas.common import SuccessEnvelope
from app.schemas.agent import (
    AgentDefinitionCreate,
    AgentDefinitionResponse,
    AgentTaskCreate,
    AgentTaskResponse,
    AgentActionCreate,
    AgentActionResponse,
    AgentApprovalRequest,
    AgentApprovalDecision,
    AgentApprovalResponse,
    RemediationProposalCreate,
    RemediationProposalResponse,
    ChangeProofV3Response,
)
from app.services.enterprise import (
    AgentGovernanceService,
    AgentTaskOrchestrator,
    AgentActionLedger,
    AgentApprovalService,
    RemediationEngine,
    ChangeProofV3Assembler,
)
from app.services.auth.service import get_current_user

router = APIRouter(prefix="/agents", tags=["Agent Governance & Orchestration"])


# ─── Agent Identity ───

@router.post("/", response_model=SuccessEnvelope[AgentDefinitionResponse], summary="Register Agent")
def register_agent(
    data: AgentDefinitionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new AI agent with governance constraints and capability enforcement."""
    agent = AgentGovernanceService.register_agent(db, data)
    return SuccessEnvelope(
        data=AgentDefinitionResponse(
            id=agent.id,
            organization_id=agent.organization_id,
            name=agent.name,
            agent_type=agent.agent_type,
            provider=agent.provider,
            model=agent.model,
            version=agent.version,
            status=agent.status,
            autonomy_level=agent.autonomy_level,
            owner_id=agent.owner_id,
            capabilities=agent.capabilities or [],
            allowed_scopes=agent.allowed_scopes or {},
            created_at=agent.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_agent"),
    )


@router.get("/", response_model=SuccessEnvelope[List[AgentDefinitionResponse]], summary="List Agents")
def list_agents(
    request: Request,
    organization_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List registered agents with optional filtering."""
    agents = AgentGovernanceService.list_agents(db, organization_id=organization_id, status=status)
    return SuccessEnvelope(
        data=[
            AgentDefinitionResponse(
                id=a.id,
                organization_id=a.organization_id,
                name=a.name,
                agent_type=a.agent_type,
                provider=a.provider,
                model=a.model,
                version=a.version,
                status=a.status,
                autonomy_level=a.autonomy_level,
                owner_id=a.owner_id,
                capabilities=a.capabilities or [],
                allowed_scopes=a.allowed_scopes or {},
                created_at=a.created_at,
            )
            for a in agents
        ],
        request_id=getattr(request.state, "request_id", "req_agents"),
    )


@router.get("/{agent_id}", response_model=SuccessEnvelope[AgentDefinitionResponse], summary="Get Agent")
def get_agent(
    agent_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve a specific agent by ID."""
    agent = AgentGovernanceService.get_agent(db, agent_id)
    if not agent:
        raise NotFoundError("Agent not found", code="AGENT_NOT_FOUND")
    return SuccessEnvelope(
        data=AgentDefinitionResponse(
            id=agent.id,
            organization_id=agent.organization_id,
            name=agent.name,
            agent_type=agent.agent_type,
            provider=agent.provider,
            model=agent.model,
            version=agent.version,
            status=agent.status,
            autonomy_level=agent.autonomy_level,
            owner_id=agent.owner_id,
            capabilities=agent.capabilities or [],
            allowed_scopes=agent.allowed_scopes or {},
            created_at=agent.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_agent"),
    )


@router.post("/{agent_id}/check-capability", summary="Check Agent Capability")
def check_capability(
    agent_id: str,
    capability: str = Query(..., description="Capability to check, e.g. READ_REPOSITORY"),
    target_organization_id: Optional[str] = Query(None, description="Optional target organization ID for tenant boundary check"),
    target_repository_id: Optional[str] = Query(None, description="Optional target repository ID for scope check"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if an agent is allowed to perform a specific capability within an optional tenant/repository scope."""
    agent = AgentGovernanceService.get_agent(db, agent_id)
    if not agent:
        raise NotFoundError("Agent not found", code="AGENT_NOT_FOUND")
    result = AgentGovernanceService.check_authorization(
        agent,
        capability,
        target_organization_id=target_organization_id,
        target_repository_id=target_repository_id,
    )
    return SuccessEnvelope(
        data=result,
        request_id=getattr(request.state, "request_id", "req_cap_check") if request else "req_cap_check",
    )


@router.post("/{agent_id}/disable", response_model=SuccessEnvelope[AgentDefinitionResponse], summary="Disable Agent")
def disable_agent(
    agent_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable an active agent, revoking all capabilities."""
    agent = AgentGovernanceService.disable_agent(db, agent_id)
    if not agent:
        raise NotFoundError("Agent not found", code="AGENT_NOT_FOUND")
    return SuccessEnvelope(
        data=AgentDefinitionResponse(
            id=agent.id,
            organization_id=agent.organization_id,
            name=agent.name,
            agent_type=agent.agent_type,
            provider=agent.provider,
            model=agent.model,
            version=agent.version,
            status=agent.status,
            autonomy_level=agent.autonomy_level,
            owner_id=agent.owner_id,
            capabilities=agent.capabilities or [],
            allowed_scopes=agent.allowed_scopes or {},
            created_at=agent.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_disable"),
    )


# ─── Agent Tasks ───

@router.post("/tasks", response_model=SuccessEnvelope[AgentTaskResponse], summary="Create Agent Task")
def create_task(
    data: AgentTaskCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new bounded agent task with budget limits."""
    task = AgentTaskOrchestrator.create_task(db, data)
    return SuccessEnvelope(
        data=AgentTaskResponse(
            id=task.id,
            organization_id=task.organization_id,
            agent_id=task.agent_id,
            change_id=task.change_id,
            analysis_run_id=task.analysis_run_id,
            task_type=task.task_type,
            status=task.status,
            initiator_type=task.initiator_type,
            initiator_id=task.initiator_id,
            plan=task.plan or {},
            result=task.result or {},
            step_count=task.step_count,
            token_count=task.token_count,
            cost_estimate=task.cost_estimate,
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_task"),
    )


@router.get("/tasks", response_model=SuccessEnvelope[List[AgentTaskResponse]], summary="List Agent Tasks")
def list_tasks(
    request: Request,
    organization_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    change_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List agent tasks with optional filtering."""
    tasks = AgentTaskOrchestrator.list_tasks(
        db, organization_id=organization_id, agent_id=agent_id,
        change_id=change_id, status=status,
    )
    return SuccessEnvelope(
        data=[
            AgentTaskResponse(
                id=t.id,
                organization_id=t.organization_id,
                agent_id=t.agent_id,
                change_id=t.change_id,
                analysis_run_id=t.analysis_run_id,
                task_type=t.task_type,
                status=t.status,
                initiator_type=t.initiator_type,
                initiator_id=t.initiator_id,
                plan=t.plan or {},
                result=t.result or {},
                step_count=t.step_count,
                token_count=t.token_count,
                cost_estimate=t.cost_estimate,
                started_at=t.started_at,
                completed_at=t.completed_at,
                created_at=t.created_at,
            )
            for t in tasks
        ],
        request_id=getattr(request.state, "request_id", "req_tasks"),
    )


@router.post("/tasks/{task_id}/start", response_model=SuccessEnvelope[AgentTaskResponse], summary="Start Task")
def start_task(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a pending task as running."""
    task = AgentTaskOrchestrator.start_task(db, task_id)
    if not task:
        raise NotFoundError("Task not found", code="TASK_NOT_FOUND")
    return SuccessEnvelope(
        data=AgentTaskResponse(
            id=task.id, organization_id=task.organization_id,
            agent_id=task.agent_id, change_id=task.change_id,
            analysis_run_id=task.analysis_run_id, task_type=task.task_type,
            status=task.status, initiator_type=task.initiator_type,
            initiator_id=task.initiator_id, plan=task.plan or {},
            result=task.result or {}, step_count=task.step_count,
            token_count=task.token_count, cost_estimate=task.cost_estimate,
            started_at=task.started_at, completed_at=task.completed_at,
            created_at=task.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_start"),
    )


@router.get("/tasks/{task_id}/budget", summary="Check Task Budget")
def check_task_budget(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check whether a task is within its step/token/cost budget."""
    task = AgentTaskOrchestrator.get_task(db, task_id)
    if not task:
        raise NotFoundError("Task not found", code="TASK_NOT_FOUND")
    budget = AgentTaskOrchestrator.check_budget(task)
    return SuccessEnvelope(
        data=budget,
        request_id=getattr(request.state, "request_id", "req_budget"),
    )


@router.get("/tasks/{task_id}/audit", summary="Get Task Audit Summary")
def get_task_audit(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get an audit summary of all actions performed within a task."""
    summary = AgentActionLedger.get_task_audit_summary(db, task_id)
    return SuccessEnvelope(
        data=summary,
        request_id=getattr(request.state, "request_id", "req_audit"),
    )


# ─── Agent Actions ───

@router.post("/actions", response_model=SuccessEnvelope[AgentActionResponse], summary="Record Action")
def record_action(
    data: AgentActionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record an agent action in the immutable audit ledger."""
    action = AgentActionLedger.record_action(db, data)
    return SuccessEnvelope(
        data=AgentActionResponse(
            id=action.id,
            task_id=action.task_id,
            agent_id=action.agent_id,
            organization_id=action.organization_id,
            repository_id=action.repository_id,
            change_id=action.change_id,
            analysis_run_id=action.analysis_run_id,
            action_type=action.action_type,
            requested_capability=action.requested_capability,
            tool_name=action.tool_name,
            input_summary=action.input_summary or {},
            output_summary=action.output_summary or {},
            policy_decision=action.policy_decision,
            status=action.status,
            created_at=action.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_action"),
    )


@router.get("/actions", response_model=SuccessEnvelope[List[AgentActionResponse]], summary="List Actions")
def list_actions(
    request: Request,
    task_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List agent actions from the audit ledger."""
    actions = AgentActionLedger.list_actions(
        db, task_id=task_id, agent_id=agent_id,
        organization_id=organization_id, limit=limit,
    )
    return SuccessEnvelope(
        data=[
            AgentActionResponse(
                id=a.id, task_id=a.task_id, agent_id=a.agent_id,
                organization_id=a.organization_id,
                repository_id=a.repository_id, change_id=a.change_id,
                analysis_run_id=a.analysis_run_id,
                action_type=a.action_type,
                requested_capability=a.requested_capability,
                tool_name=a.tool_name,
                input_summary=a.input_summary or {},
                output_summary=a.output_summary or {},
                policy_decision=a.policy_decision,
                status=a.status, created_at=a.created_at,
            )
            for a in actions
        ],
        request_id=getattr(request.state, "request_id", "req_actions"),
    )


# ─── Approvals ───

@router.post("/approvals", response_model=SuccessEnvelope[AgentApprovalResponse], summary="Request Approval")
def request_approval(
    data: AgentApprovalRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a human-in-the-loop approval request for a high-risk agent action."""
    approval = AgentApprovalService.create_approval_request(db, data)
    return SuccessEnvelope(
        data=AgentApprovalResponse(
            id=approval.id,
            organization_id=approval.organization_id,
            task_id=approval.task_id,
            change_id=approval.change_id,
            requesting_agent_id=approval.requesting_agent_id,
            requested_action=approval.requested_action,
            risk_level=approval.risk_level,
            affected_resources=approval.affected_resources or [],
            evidence_summary=approval.evidence_summary or {},
            status=approval.status,
            approver_user_id=approval.approver_user_id,
            decision_reason=approval.decision_reason,
            decided_at=approval.decided_at,
            created_at=approval.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_approval"),
    )


@router.post("/approvals/{approval_id}/decide", response_model=SuccessEnvelope[AgentApprovalResponse], summary="Decide Approval")
def decide_approval(
    approval_id: str,
    decision: AgentApprovalDecision,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve or reject a pending agent action approval request."""
    try:
        approval = AgentApprovalService.decide_approval(
            db, approval_id, decision, approver_user_id=current_user.id
        )
    except ValueError as e:
        raise BadRequestError(str(e), code="INVALID_APPROVAL_ACTION")
    if not approval:
        raise NotFoundError("Approval not found or already decided", code="APPROVAL_NOT_FOUND")
    return SuccessEnvelope(
        data=AgentApprovalResponse(
            id=approval.id,
            organization_id=approval.organization_id,
            task_id=approval.task_id,
            change_id=approval.change_id,
            requesting_agent_id=approval.requesting_agent_id,
            requested_action=approval.requested_action,
            risk_level=approval.risk_level,
            affected_resources=approval.affected_resources or [],
            evidence_summary=approval.evidence_summary or {},
            status=approval.status,
            approver_user_id=approval.approver_user_id,
            decision_reason=approval.decision_reason,
            decided_at=approval.decided_at,
            created_at=approval.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_decide"),
    )


@router.post("/approvals/{approval_id}/expire", response_model=SuccessEnvelope[AgentApprovalResponse], summary="Expire Approval")
def expire_approval(
    approval_id: str,
    request: Request,
    reason: str = Query("Approval expired due to timeout", description="Expiration reason"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a pending approval request as expired."""
    approval = AgentApprovalService.expire_approval(db, approval_id, reason=reason)
    if not approval:
        raise NotFoundError("Approval not found or not pending", code="APPROVAL_NOT_FOUND")
    return SuccessEnvelope(
        data=AgentApprovalResponse(
            id=approval.id,
            organization_id=approval.organization_id,
            task_id=approval.task_id,
            change_id=approval.change_id,
            requesting_agent_id=approval.requesting_agent_id,
            requested_action=approval.requested_action,
            risk_level=approval.risk_level,
            affected_resources=approval.affected_resources or [],
            evidence_summary=approval.evidence_summary or {},
            status=approval.status,
            approver_user_id=approval.approver_user_id,
            decision_reason=approval.decision_reason,
            decided_at=approval.decided_at,
            created_at=approval.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_expire"),
    )


@router.get("/approvals/pending", response_model=SuccessEnvelope[List[AgentApprovalResponse]], summary="List Pending Approvals")
def list_pending_approvals(
    request: Request,
    organization_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all pending approval requests awaiting human decision."""
    approvals = AgentApprovalService.list_pending_approvals(db, organization_id=organization_id)
    return SuccessEnvelope(
        data=[
            AgentApprovalResponse(
                id=a.id, organization_id=a.organization_id,
                task_id=a.task_id, change_id=a.change_id,
                requesting_agent_id=a.requesting_agent_id,
                requested_action=a.requested_action,
                risk_level=a.risk_level,
                affected_resources=a.affected_resources or [],
                evidence_summary=a.evidence_summary or {},
                status=a.status, approver_user_id=a.approver_user_id,
                decision_reason=a.decision_reason,
                decided_at=a.decided_at, created_at=a.created_at,
            )
            for a in approvals
        ],
        request_id=getattr(request.state, "request_id", "req_pending"),
    )


# ─── Remediation ───

@router.post("/remediations", response_model=SuccessEnvelope[RemediationProposalResponse], summary="Create Remediation")
def create_remediation(
    data: RemediationProposalCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a remediation proposal with automatic before/after risk verification."""
    proposal = RemediationEngine.create_proposal(db, data)
    return SuccessEnvelope(
        data=RemediationProposalResponse(
            id=proposal.id,
            organization_id=proposal.organization_id,
            change_id=proposal.change_id,
            agent_id=proposal.agent_id,
            title=proposal.title,
            description=proposal.description,
            original_risk_score=proposal.original_risk_score,
            original_risk_level=proposal.original_risk_level,
            proposed_diff=proposal.proposed_diff,
            explanation=proposal.explanation,
            affected_components=proposal.affected_components or [],
            verified_risk_score=proposal.verified_risk_score,
            verified_risk_level=proposal.verified_risk_level,
            verification_status=proposal.verification_status,
            verification_evidence=proposal.verification_evidence or {},
            approval_id=proposal.approval_id,
            created_at=proposal.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_remediation"),
    )


@router.get("/remediations", response_model=SuccessEnvelope[List[RemediationProposalResponse]], summary="List Remediations")
def list_remediations(
    request: Request,
    organization_id: Optional[str] = Query(None),
    change_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List remediation proposals with optional filtering."""
    proposals = RemediationEngine.list_proposals(db, organization_id=organization_id, change_id=change_id)
    return SuccessEnvelope(
        data=[
            RemediationProposalResponse(
                id=p.id, organization_id=p.organization_id,
                change_id=p.change_id, agent_id=p.agent_id,
                title=p.title, description=p.description,
                original_risk_score=p.original_risk_score,
                original_risk_level=p.original_risk_level,
                proposed_diff=p.proposed_diff, explanation=p.explanation,
                affected_components=p.affected_components or [],
                verified_risk_score=p.verified_risk_score,
                verified_risk_level=p.verified_risk_level,
                verification_status=p.verification_status,
                verification_evidence=p.verification_evidence or {},
                approval_id=p.approval_id, created_at=p.created_at,
            )
            for p in proposals
        ],
        request_id=getattr(request.state, "request_id", "req_remediations"),
    )


# ─── Change Proof v3 ───

@router.post("/proof-v3/{change_id}/{analysis_run_id}", response_model=SuccessEnvelope[ChangeProofV3Response], summary="Assemble Change Proof v3")
def assemble_proof_v3(
    change_id: str,
    analysis_run_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assemble the canonical Phase 5 Change Proof v3, unifying all assurance signals across all phases."""
    proof = ChangeProofV3Assembler.assemble(db, change_id, analysis_run_id)
    return SuccessEnvelope(
        data=ChangeProofV3Response(
            id=proof.id,
            change_id=proof.change_id,
            analysis_run_id=proof.analysis_run_id,
            version=proof.version,
            overall_verdict=proof.overall_verdict,
            risk_level=proof.risk_level,
            risk_score=proof.risk_score,
            proof_document=proof.proof_document,
            created_at=proof.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_proof_v3"),
    )


@router.get("/proof-v3/{change_id}", response_model=SuccessEnvelope[ChangeProofV3Response], summary="Get Change Proof v3")
def get_proof_v3(
    change_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the latest Change Proof v3 for a given change."""
    from app.models.agent import ChangeProofV3
    proof = db.query(ChangeProofV3).filter(ChangeProofV3.change_id == change_id).order_by(ChangeProofV3.created_at.desc()).first()
    if not proof:
        raise NotFoundError("Change Proof v3 not found for this change", code="PROOF_NOT_FOUND")
    return SuccessEnvelope(
        data=ChangeProofV3Response(
            id=proof.id,
            change_id=proof.change_id,
            analysis_run_id=proof.analysis_run_id,
            version=proof.version,
            overall_verdict=proof.overall_verdict,
            risk_level=proof.risk_level,
            risk_score=proof.risk_score,
            proof_document=proof.proof_document,
            created_at=proof.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_get_proof_v3"),
    )

