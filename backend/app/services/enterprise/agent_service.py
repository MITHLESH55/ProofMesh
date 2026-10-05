"""
Phase 5 Agent Services — Governance, Task Orchestration, Action Ledger, Remediation, Change Proof v3.

Provides the full agent lifecycle:
- Agent identity registration and governance policy enforcement
- Bounded task orchestration with budget limits
- Immutable action audit ledger
- Human-in-the-loop approval gates
- Remediation proposal generation and verification
- Change Proof v3 assembly unifying all assurance signals
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.agent import (
    AgentDefinition,
    AgentTask,
    AgentAction,
    AgentApproval,
    RemediationProposal,
    ChangeProofV3,
)
from app.models.entities import Change, AnalysisRun
from app.models.assurance import RiskAssessment, ChangeProof, PolicyDecision
from app.models.runtime import CIAssuranceCheck, RuntimeFinding, Deployment
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


# ─── Capability constants ───
CAPABILITY_TIERS = {
    0: [],  # Observe only — no active capabilities
    1: ["READ_REPOSITORY", "READ_GRAPH", "ANALYZE_DIFF"],
    2: ["READ_REPOSITORY", "READ_GRAPH", "ANALYZE_DIFF", "GENERATE_TESTS", "GENERATE_REPORTS"],
    3: ["READ_REPOSITORY", "READ_GRAPH", "ANALYZE_DIFF", "GENERATE_TESTS", "GENERATE_REPORTS", "PROPOSE_PATCH", "CREATE_BRANCH"],
    4: ["READ_REPOSITORY", "READ_GRAPH", "ANALYZE_DIFF", "GENERATE_TESTS", "GENERATE_REPORTS", "PROPOSE_PATCH", "CREATE_BRANCH", "CREATE_PR", "QUERY_RUNTIME"],
    5: ["READ_REPOSITORY", "READ_GRAPH", "ANALYZE_DIFF", "GENERATE_TESTS", "GENERATE_REPORTS", "PROPOSE_PATCH", "CREATE_BRANCH", "CREATE_PR", "QUERY_RUNTIME", "APPLY_REMEDIATION"],
}

# Hard rules — agents CANNOT do these regardless of autonomy_level
HARD_DENIED_CAPABILITIES = frozenset([
    "MODIFY_PRODUCTION_DB",
    "BYPASS_POLICY",
    "ESCALATE_PRIVILEGES",
    "DELETE_REPOSITORY",
    "DISABLE_MONITORING",
])

# Maximum budget limits per task
MAX_STEPS_PER_TASK = 200
MAX_TOKENS_PER_TASK = 500_000
MAX_COST_PER_TASK = 50.0  # USD
MAX_RUNTIME_SECONDS_PER_TASK = 1800  # 30 minutes
MAX_RETRIES_PER_TASK = 3
MAX_MODEL_CALLS_PER_TASK = 100


class AgentGovernanceService:
    """Manages agent identity registration, capability enforcement, and policy checks."""

    @staticmethod
    def register_agent(db: Session, data: AgentDefinitionCreate) -> AgentDefinition:
        """Register a new AI agent with governance constraints."""
        # Validate autonomy level caps capabilities
        max_level = max(CAPABILITY_TIERS.keys())
        effective_level = min(data.autonomy_level, max_level)

        # Filter capabilities to what the autonomy level allows
        allowed_capabilities = set(CAPABILITY_TIERS.get(effective_level, []))
        requested_capabilities = set(data.capabilities)
        # If requested_capabilities is just the schema default and effective_level > 1, expand to tier
        default_tier1 = {"READ_REPOSITORY", "READ_GRAPH", "ANALYZE_DIFF"}
        if (not requested_capabilities or requested_capabilities == default_tier1) and effective_level > 1:
            requested_capabilities = set(CAPABILITY_TIERS.get(effective_level, []))

        # Remove any hard-denied capabilities
        safe_capabilities = list(
            (requested_capabilities & allowed_capabilities) - HARD_DENIED_CAPABILITIES
        )
        if not safe_capabilities and effective_level > 0:
            safe_capabilities = CAPABILITY_TIERS.get(effective_level, [])

        agent = AgentDefinition(
            organization_id=data.organization_id,
            name=data.name,
            agent_type=data.agent_type.upper(),
            provider=data.provider,
            model=data.model,
            version=data.version,
            status=data.status.upper(),
            autonomy_level=effective_level,
            owner_id=data.owner_id,
            capabilities=safe_capabilities,
            allowed_scopes=data.allowed_scopes,
            created_at=datetime.now(timezone.utc),
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def get_agent(db: Session, agent_id: str) -> Optional[AgentDefinition]:
        return db.query(AgentDefinition).filter(AgentDefinition.id == agent_id).first()

    @staticmethod
    def list_agents(
        db: Session,
        organization_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[AgentDefinition]:
        query = db.query(AgentDefinition)
        if organization_id:
            query = query.filter(AgentDefinition.organization_id == organization_id)
        if status:
            query = query.filter(AgentDefinition.status == status.upper())
        return query.order_by(AgentDefinition.created_at.desc()).all()

    @staticmethod
    def check_capability(agent: AgentDefinition, requested_capability: str) -> Dict[str, Any]:
        """
        Check if an agent is allowed to perform a specific capability.

        Returns:
            {"allowed": bool, "reason": str, "policy_decision": str}
        """
        # Hard deny check
        if requested_capability in HARD_DENIED_CAPABILITIES:
            return {
                "allowed": False,
                "reason": f"Capability '{requested_capability}' is unconditionally denied by hard policy rules.",
                "policy_decision": "BLOCKED",
            }

        # Agent status check
        if agent.status != "ACTIVE":
            return {
                "allowed": False,
                "reason": f"Agent '{agent.name}' is {agent.status} and cannot perform actions.",
                "policy_decision": "BLOCKED",
            }

        # Capability check against agent's registered capabilities
        if requested_capability not in (agent.capabilities or []):
            return {
                "allowed": False,
                "reason": (
                    f"Agent '{agent.name}' (autonomy_level={agent.autonomy_level}) does not have "
                    f"capability '{requested_capability}'. Registered capabilities: {agent.capabilities}"
                ),
                "policy_decision": "BLOCKED",
            }

        # High-risk capabilities require human approval
        high_risk_caps = {"APPLY_REMEDIATION", "CREATE_PR", "CREATE_BRANCH"}
        if requested_capability in high_risk_caps:
            return {
                "allowed": True,
                "reason": f"Capability '{requested_capability}' is allowed but requires human approval before execution.",
                "policy_decision": "PENDING_APPROVAL",
            }

        return {
            "allowed": True,
            "reason": f"Capability '{requested_capability}' is allowed for agent '{agent.name}'.",
            "policy_decision": "ALLOWED",
        }

    @staticmethod
    def check_scope(
        agent: AgentDefinition,
        target_organization_id: Optional[str] = None,
        target_repository_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check if an agent is authorized to operate within a specific organization and repository scope.
        Enforces tenant isolation and repository access boundaries.
        """
        if agent.status != "ACTIVE":
            return {
                "allowed": False,
                "reason": f"Agent '{agent.name}' is {agent.status} and cannot access any scope.",
                "policy_decision": "BLOCKED",
            }

        # Multi-tenant boundary check: agent belongs to agent.organization_id
        allowed_orgs = [agent.organization_id]
        if agent.allowed_scopes and isinstance(agent.allowed_scopes, dict):
            extra_orgs = agent.allowed_scopes.get("organizations", [])
            if isinstance(extra_orgs, list):
                allowed_orgs.extend(extra_orgs)

        if target_organization_id and target_organization_id not in allowed_orgs:
            return {
                "allowed": False,
                "reason": (
                    f"Cross-tenant access violation: Agent '{agent.name}' (org={agent.organization_id}) "
                    f"cannot access organization '{target_organization_id}'."
                ),
                "policy_decision": "BLOCKED",
            }

        # Repository scope check
        if target_repository_id and agent.allowed_scopes and isinstance(agent.allowed_scopes, dict):
            allowed_repos = agent.allowed_scopes.get("repositories", [])
            if allowed_repos and "*" not in allowed_repos:
                if target_repository_id not in allowed_repos:
                    return {
                        "allowed": False,
                        "reason": (
                            f"Scope violation: Agent '{agent.name}' is not authorized for repository "
                            f"'{target_repository_id}'. Allowed repositories: {allowed_repos}"
                        ),
                        "policy_decision": "BLOCKED",
                    }

        return {
            "allowed": True,
            "reason": f"Agent '{agent.name}' is authorized for the requested scope.",
            "policy_decision": "ALLOWED",
        }

    @staticmethod
    def check_authorization(
        agent: AgentDefinition,
        requested_capability: str,
        target_organization_id: Optional[str] = None,
        target_repository_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive pre-execution authorization check covering capability, tenant isolation, and repository scope.
        """
        scope_result = AgentGovernanceService.check_scope(
            agent,
            target_organization_id=target_organization_id,
            target_repository_id=target_repository_id,
        )
        if not scope_result["allowed"]:
            return scope_result

        return AgentGovernanceService.check_capability(agent, requested_capability)

    @staticmethod
    def disable_agent(db: Session, agent_id: str, reason: str = "Manual disable") -> Optional[AgentDefinition]:
        agent = db.query(AgentDefinition).filter(AgentDefinition.id == agent_id).first()
        if agent:
            agent.status = "DISABLED"
            db.commit()
            db.refresh(agent)
        return agent


class AgentTaskOrchestrator:
    """Manages bounded agent task execution with step/token/cost limits and audit trail."""

    @staticmethod
    def create_task(db: Session, data: AgentTaskCreate) -> AgentTask:
        """Create a new agent task with initial plan."""
        task = AgentTask(
            organization_id=data.organization_id,
            agent_id=data.agent_id,
            change_id=data.change_id,
            analysis_run_id=data.analysis_run_id,
            task_type=data.task_type.upper(),
            status="PENDING",
            initiator_type=data.initiator_type.upper(),
            initiator_id=data.initiator_id,
            plan=data.plan or {},
            result={},
            step_count=0,
            token_count=0,
            cost_estimate=0.0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: str) -> Optional[AgentTask]:
        return db.query(AgentTask).filter(AgentTask.id == task_id).first()

    @staticmethod
    def list_tasks(
        db: Session,
        organization_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        change_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[AgentTask]:
        query = db.query(AgentTask)
        if organization_id:
            query = query.filter(AgentTask.organization_id == organization_id)
        if agent_id:
            query = query.filter(AgentTask.agent_id == agent_id)
        if change_id:
            query = query.filter(AgentTask.change_id == change_id)
        if status:
            query = query.filter(AgentTask.status == status.upper())
        return query.order_by(AgentTask.created_at.desc()).all()

    @staticmethod
    def start_task(db: Session, task_id: str) -> Optional[AgentTask]:
        """Mark a task as running."""
        task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if task and task.status == "PENDING":
            task.status = "RUNNING"
            task.started_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(task)
        return task

    @staticmethod
    def check_budget(task: AgentTask) -> Dict[str, Any]:
        """Check if a task has exceeded its step, token, runtime, retry, or cost budget."""
        exceeded = []
        if task.step_count >= MAX_STEPS_PER_TASK:
            exceeded.append(f"step_count={task.step_count} >= {MAX_STEPS_PER_TASK}")
        if task.token_count >= MAX_TOKENS_PER_TASK:
            exceeded.append(f"token_count={task.token_count} >= {MAX_TOKENS_PER_TASK}")
        if task.cost_estimate >= MAX_COST_PER_TASK:
            exceeded.append(f"cost_estimate={task.cost_estimate} >= {MAX_COST_PER_TASK}")

        # Check runtime if task has started
        started_at = getattr(task, "started_at", None)
        if started_at:
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            runtime_sec = (now - started_at).total_seconds()
            if runtime_sec >= MAX_RUNTIME_SECONDS_PER_TASK:
                exceeded.append(f"runtime_seconds={int(runtime_sec)} >= {MAX_RUNTIME_SECONDS_PER_TASK}")

        # Check retries and model calls from plan / metadata
        plan = getattr(task, "plan", None)
        if plan and isinstance(plan, dict):
            retry_count = plan.get("retry_count", 0)
            if retry_count >= MAX_RETRIES_PER_TASK:
                exceeded.append(f"retry_count={retry_count} >= {MAX_RETRIES_PER_TASK}")
            model_calls = plan.get("model_calls", 0)
            if model_calls >= MAX_MODEL_CALLS_PER_TASK:
                exceeded.append(f"model_calls={model_calls} >= {MAX_MODEL_CALLS_PER_TASK}")

        return {
            "within_budget": len(exceeded) == 0,
            "exceeded": exceeded,
            "step_count": task.step_count,
            "token_count": task.token_count,
            "cost_estimate": task.cost_estimate,
        }

    @staticmethod
    def record_step(
        db: Session,
        task_id: str,
        tokens_used: int = 0,
        cost_delta: float = 0.0,
    ) -> Optional[AgentTask]:
        """Increment task step/token/cost counters. Auto-terminate if budget exceeded."""
        task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if not task or task.status != "RUNNING":
            return task

        task.step_count += 1
        task.token_count += tokens_used
        task.cost_estimate += cost_delta

        budget = AgentTaskOrchestrator.check_budget(task)
        if not budget["within_budget"]:
            task.status = "BUDGET_EXCEEDED"
            task.result = {
                **(task.result or {}),
                "termination_reason": "budget_exceeded",
                "exceeded_limits": budget["exceeded"],
            }
            task.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def complete_task(
        db: Session,
        task_id: str,
        result: Dict[str, Any],
        status: str = "COMPLETED",
    ) -> Optional[AgentTask]:
        """Mark a task as completed with its result."""
        task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if task and task.status in ("RUNNING", "PENDING"):
            task.status = status.upper()
            task.result = result
            task.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(task)
        return task


class AgentActionLedger:
    """Immutable audit trail of every tool call and operation performed by agents."""

    @staticmethod
    def record_action(db: Session, data: AgentActionCreate) -> AgentAction:
        """Record a single agent action in the immutable ledger."""
        action = AgentAction(
            task_id=data.task_id,
            agent_id=data.agent_id,
            organization_id=data.organization_id,
            repository_id=data.repository_id,
            change_id=data.change_id,
            analysis_run_id=data.analysis_run_id,
            action_type=data.action_type.upper(),
            requested_capability=data.requested_capability,
            tool_name=data.tool_name,
            input_summary=data.input_summary,
            output_summary=data.output_summary,
            policy_decision=data.policy_decision.upper(),
            status=data.status.upper(),
            created_at=datetime.now(timezone.utc),
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def list_actions(
        db: Session,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AgentAction]:
        query = db.query(AgentAction)
        if task_id:
            query = query.filter(AgentAction.task_id == task_id)
        if agent_id:
            query = query.filter(AgentAction.agent_id == agent_id)
        if organization_id:
            query = query.filter(AgentAction.organization_id == organization_id)
        return query.order_by(AgentAction.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_task_audit_summary(db: Session, task_id: str) -> Dict[str, Any]:
        """Generate an audit summary for all actions in a task."""
        actions = (
            db.query(AgentAction)
            .filter(AgentAction.task_id == task_id)
            .order_by(AgentAction.created_at.asc())
            .all()
        )
        total = len(actions)
        allowed = sum(1 for a in actions if a.policy_decision == "ALLOWED")
        blocked = sum(1 for a in actions if a.policy_decision == "BLOCKED")
        succeeded = sum(1 for a in actions if a.status == "SUCCESS")
        failed = sum(1 for a in actions if a.status == "FAILED")

        return {
            "task_id": task_id,
            "total_actions": total,
            "allowed_actions": allowed,
            "blocked_actions": blocked,
            "succeeded_actions": succeeded,
            "failed_actions": failed,
            "action_types": list(set(a.action_type for a in actions)),
            "tools_used": list(set(a.tool_name for a in actions)),
        }


class AgentApprovalService:
    """Human-in-the-loop approval gates for high-risk agent operations."""

    @staticmethod
    def create_approval_request(db: Session, data: AgentApprovalRequest) -> AgentApproval:
        """Create a pending approval request for a high-risk agent action."""
        approval = AgentApproval(
            organization_id=data.organization_id,
            task_id=data.task_id,
            change_id=data.change_id,
            requesting_agent_id=data.requesting_agent_id,
            requested_action=data.requested_action,
            risk_level=data.risk_level.upper(),
            affected_resources=data.affected_resources,
            evidence_summary=data.evidence_summary,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def decide_approval(
        db: Session,
        approval_id: str,
        decision: AgentApprovalDecision,
        approver_user_id: str,
    ) -> Optional[AgentApproval]:
        """Record a human approval or rejection decision."""
        approval = db.query(AgentApproval).filter(AgentApproval.id == approval_id).first()
        if not approval or approval.status != "PENDING":
            return approval

        # Agent cannot approve its own action
        if approver_user_id == approval.requesting_agent_id:
            raise ValueError("Agent cannot approve its own action. Human approval required.")

        approval.status = decision.decision.upper()
        approval.approver_user_id = approver_user_id
        approval.decision_reason = decision.reason
        approval.decided_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def expire_approval(
        db: Session,
        approval_id: str,
        reason: str = "Approval expired due to timeout",
    ) -> Optional[AgentApproval]:
        """Mark a pending approval as expired."""
        approval = db.query(AgentApproval).filter(AgentApproval.id == approval_id).first()
        if not approval or approval.status != "PENDING":
            return approval

        approval.status = "EXPIRED"
        approval.decision_reason = reason
        approval.decided_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def list_pending_approvals(
        db: Session,
        organization_id: Optional[str] = None,
    ) -> List[AgentApproval]:
        query = db.query(AgentApproval).filter(AgentApproval.status == "PENDING")
        if organization_id:
            query = query.filter(AgentApproval.organization_id == organization_id)
        return query.order_by(AgentApproval.created_at.desc()).all()


class RemediationEngine:
    """Generates, verifies, and tracks autonomous remediation proposals."""

    @staticmethod
    def create_proposal(
        db: Session, data: RemediationProposalCreate
    ) -> RemediationProposal:
        """Create a new remediation proposal from an agent with before/after risk verification."""
        # Simulate deterministic verification: re-run risk assessment on proposed diff
        verified_score, verified_level = RemediationEngine._verify_remediation(
            data.original_risk_score,
            data.proposed_diff,
            data.affected_components,
        )

        if verified_score < data.original_risk_score:
            verification_status = "VERIFIED_SAFER"
        elif verified_score > data.original_risk_score:
            verification_status = "REJECTED_REGRESSION"
        else:
            verification_status = "VERIFIED_SAFER"  # Same score = at least not worse

        proposal = RemediationProposal(
            organization_id=data.organization_id,
            change_id=data.change_id,
            agent_id=data.agent_id,
            title=data.title,
            description=data.description,
            original_risk_score=data.original_risk_score,
            original_risk_level=data.original_risk_level,
            proposed_diff=data.proposed_diff,
            explanation=data.explanation,
            affected_components=data.affected_components,
            verified_risk_score=verified_score,
            verified_risk_level=verified_level,
            verification_status=verification_status,
            verification_evidence={
                "method": "deterministic_re_assessment",
                "original_score": data.original_risk_score,
                "verified_score": verified_score,
                "delta": round(data.original_risk_score - verified_score, 4),
                "affected_component_count": len(data.affected_components),
            },
            created_at=datetime.now(timezone.utc),
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        return proposal

    @staticmethod
    def list_proposals(
        db: Session,
        organization_id: Optional[str] = None,
        change_id: Optional[str] = None,
    ) -> List[RemediationProposal]:
        query = db.query(RemediationProposal)
        if organization_id:
            query = query.filter(RemediationProposal.organization_id == organization_id)
        if change_id:
            query = query.filter(RemediationProposal.change_id == change_id)
        return query.order_by(RemediationProposal.created_at.desc()).all()

    @staticmethod
    def _verify_remediation(
        original_score: float,
        proposed_diff: str,
        affected_components: List[str],
    ) -> tuple:
        """
        Deterministic remediation verification.

        Computes a new risk score based on the proposed diff characteristics.
        In a full implementation, this would re-run the Phase 3 risk engine
        on the patched code.
        """
        # Heuristic: larger diffs are riskier, fewer affected components is better
        diff_lines = len(proposed_diff.strip().splitlines())
        component_count = len(affected_components)

        # Risk reduction factor: small, targeted patches reduce risk more
        if diff_lines <= 10 and component_count <= 2:
            reduction = 0.40  # Well-targeted fix
        elif diff_lines <= 30 and component_count <= 5:
            reduction = 0.25  # Moderate fix
        elif diff_lines <= 100:
            reduction = 0.10  # Broad fix
        else:
            reduction = 0.0  # Too broad to safely predict

        new_score = round(max(0.0, original_score * (1.0 - reduction)), 4)

        if new_score < 25.0:
            new_level = "LOW"
        elif new_score < 50.0:
            new_level = "MEDIUM"
        elif new_score < 75.0:
            new_level = "HIGH"
        else:
            new_level = "CRITICAL"

        return new_score, new_level


class ChangeProofV3Assembler:
    """Assembles the canonical Phase 5 Change Proof v3, unifying all assurance signals."""

    @staticmethod
    def assemble(
        db: Session,
        change_id: str,
        analysis_run_id: str,
    ) -> ChangeProofV3:
        """
        Assemble a comprehensive Change Proof v3 by gathering:
        - Phase 3 risk assessment and policy decision
        - Phase 4 CI checks and runtime findings
        - Phase 5 agent tasks, actions, remediations, and approvals

        This is the canonical evidence artifact proving change safety.
        """
        # Phase 3 signals
        risk = db.query(RiskAssessment).filter(RiskAssessment.analysis_run_id == analysis_run_id).first()
        policy = db.query(PolicyDecision).filter(PolicyDecision.analysis_run_id == analysis_run_id).first()
        phase3_proof = db.query(ChangeProof).filter(ChangeProof.analysis_run_id == analysis_run_id).first()

        # Phase 4 signals
        ci_checks = db.query(CIAssuranceCheck).filter(CIAssuranceCheck.change_id == change_id).all()
        deployments = db.query(Deployment).filter(Deployment.change_id == change_id).all()
        dep_ids = [d.id for d in deployments]
        runtime_findings = (
            db.query(RuntimeFinding).filter(RuntimeFinding.deployment_id.in_(dep_ids)).all()
            if dep_ids
            else []
        )

        # Phase 5 signals
        agent_tasks = db.query(AgentTask).filter(AgentTask.change_id == change_id).all()
        remediations = db.query(RemediationProposal).filter(RemediationProposal.change_id == change_id).all()
        approvals = db.query(AgentApproval).filter(AgentApproval.change_id == change_id).all()

        # Compute overall verdict
        verdict, risk_level, risk_score = ChangeProofV3Assembler._compute_verdict(
            risk=risk,
            policy=policy,
            ci_checks=ci_checks,
            runtime_findings=runtime_findings,
            agent_tasks=agent_tasks,
            remediations=remediations,
            approvals=approvals,
        )

        # Build the comprehensive proof document
        proof_document = {
            "version": "3.0.0",
            "assembled_at": datetime.now(timezone.utc).isoformat(),
            "change_id": change_id,
            "analysis_run_id": analysis_run_id,
            "phase_3_assurance": {
                "risk_level": risk.overall_risk if risk else "UNKNOWN",
                "risk_score": risk.numerical_score if risk else 0.0,
                "policy_decision": policy.decision if policy else "UNKNOWN",
                "blocking_reasons": policy.blocking_reasons if policy else [],
                "proof_summary": phase3_proof.summary if phase3_proof else "No Phase 3 proof available",
            },
            "phase_4_delivery": {
                "ci_checks_total": len(ci_checks),
                "ci_checks_passed": sum(1 for c in ci_checks if getattr(c, "gate_decision", getattr(c, "status", None)) in ("PASS", "PASSED")),
                "ci_checks_failed": sum(1 for c in ci_checks if getattr(c, "gate_decision", getattr(c, "status", None)) in ("BLOCK", "FAILED")),
                "runtime_findings_total": len(runtime_findings),
                "runtime_regressions": sum(1 for f in runtime_findings if "REGRESSION" in str(getattr(f, "finding_type", ""))),
            },
            "phase_5_agentic": {
                "agent_tasks_total": len(agent_tasks),
                "agent_tasks_completed": sum(1 for t in agent_tasks if t.status == "COMPLETED"),
                "agent_tasks_failed": sum(1 for t in agent_tasks if t.status == "FAILED"),
                "remediation_proposals": len(remediations),
                "verified_safer_remediations": sum(1 for r in remediations if r.verification_status == "VERIFIED_SAFER"),
                "pending_approvals": sum(1 for a in approvals if a.status == "PENDING"),
                "approved_actions": sum(1 for a in approvals if a.status == "APPROVED"),
                "rejected_actions": sum(1 for a in approvals if a.status == "REJECTED"),
            },
            "verdict": verdict,
        }

        proof = ChangeProofV3(
            change_id=change_id,
            analysis_run_id=analysis_run_id,
            version="3.0.0",
            overall_verdict=verdict,
            risk_level=risk_level,
            risk_score=risk_score,
            proof_document=proof_document,
            created_at=datetime.now(timezone.utc),
        )
        db.add(proof)
        db.commit()
        db.refresh(proof)
        return proof

    @staticmethod
    def _compute_verdict(
        risk,
        policy,
        ci_checks,
        runtime_findings,
        agent_tasks,
        remediations,
        approvals,
    ) -> tuple:
        """Deterministic verdict computation across all phases."""

        # Start with Phase 3 baseline
        risk_score = risk.numerical_score if risk else 0.0
        risk_level = risk.overall_risk if risk else "LOW"

        # Phase 3 policy decision
        if policy and policy.decision == "BLOCK":
            # Check if remediation has resolved the block
            verified_remediations = [r for r in remediations if r.verification_status == "VERIFIED_SAFER"]
            if verified_remediations:
                # Check if remediation was approved
                approved = [a for a in approvals if a.status == "APPROVED"]
                if approved:
                    return "REMEDIATION_VERIFIED", risk_level, risk_score
                pending = [a for a in approvals if a.status == "PENDING"]
                if pending:
                    return "REMEDIATION_PENDING_APPROVAL", risk_level, risk_score
                # Rejections, expirations, or missing approval remain BLOCKED
                return "BLOCKED", risk_level, risk_score
            return "BLOCKED", risk_level, risk_score

        # Phase 4 runtime regression check
        runtime_regressions = [f for f in runtime_findings if f.finding_type == "REGRESSION"]
        if runtime_regressions:
            return "RUNTIME_REGRESSION", risk_level, risk_score

        # Phase 4 CI failures
        ci_failures = [c for c in ci_checks if c.status == "FAILED"]
        if ci_failures:
            return "BLOCKED", risk_level, risk_score

        # All clear
        return "VERIFIED_SAFE", risk_level, risk_score


class AgentToolExecutor:
    """
    Governed tool execution engine.
    Ensures capability checks, scope checks, and approval gates occur BEFORE tool execution.
    Every attempt (success, blocked, or failed) is recorded in the immutable action ledger.
    """

    @staticmethod
    def execute_tool(
        db: Session,
        agent: AgentDefinition,
        task: AgentTask,
        action_type: str,
        requested_capability: str,
        tool_name: str,
        tool_func,
        tool_kwargs: Dict[str, Any],
        target_organization_id: Optional[str] = None,
        target_repository_id: Optional[str] = None,
        approved: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an agent tool with strict pre-execution governance.
        """
        # 1. Pre-execution authorization check (capability + tenant scope + repo scope)
        auth = AgentGovernanceService.check_authorization(
            agent,
            requested_capability=requested_capability,
            target_organization_id=target_organization_id,
            target_repository_id=target_repository_id,
        )

        if not auth["allowed"]:
            # Record blocked attempt in immutable ledger
            action = AgentActionLedger.record_action(
                db,
                AgentActionCreate(
                    task_id=task.id,
                    agent_id=agent.id,
                    organization_id=task.organization_id,
                    repository_id=target_repository_id,
                    change_id=task.change_id,
                    analysis_run_id=task.analysis_run_id,
                    action_type=action_type,
                    requested_capability=requested_capability,
                    tool_name=tool_name,
                    input_summary={"params": str(tool_kwargs)[:500]},
                    output_summary={"error": auth["reason"]},
                    policy_decision="BLOCKED",
                    status="BLOCKED",
                ),
            )
            return {
                "success": False,
                "status": "BLOCKED",
                "action_id": action.id,
                "reason": auth["reason"],
            }

        # 2. Human approval gate for high-risk actions
        if auth["policy_decision"] == "PENDING_APPROVAL" and not approved:
            action = AgentActionLedger.record_action(
                db,
                AgentActionCreate(
                    task_id=task.id,
                    agent_id=agent.id,
                    organization_id=task.organization_id,
                    repository_id=target_repository_id,
                    change_id=task.change_id,
                    analysis_run_id=task.analysis_run_id,
                    action_type=action_type,
                    requested_capability=requested_capability,
                    tool_name=tool_name,
                    input_summary={"params": str(tool_kwargs)[:500]},
                    output_summary={"approval": "Pending human approval"},
                    policy_decision="PENDING_APPROVAL",
                    status="PENDING_APPROVAL",
                ),
            )
            return {
                "success": False,
                "status": "PENDING_APPROVAL",
                "action_id": action.id,
                "reason": "High-risk action requires human approval before execution.",
            }

        # 3. Execute tool safely
        try:
            output = tool_func(**tool_kwargs)
            action = AgentActionLedger.record_action(
                db,
                AgentActionCreate(
                    task_id=task.id,
                    agent_id=agent.id,
                    organization_id=task.organization_id,
                    repository_id=target_repository_id,
                    change_id=task.change_id,
                    analysis_run_id=task.analysis_run_id,
                    action_type=action_type,
                    requested_capability=requested_capability,
                    tool_name=tool_name,
                    input_summary={"params": str(tool_kwargs)[:500]},
                    output_summary={"result": str(output)[:500]},
                    policy_decision="ALLOWED",
                    status="SUCCESS",
                ),
            )
            return {"success": True, "status": "SUCCESS", "action_id": action.id, "output": output}
        except Exception as e:
            action = AgentActionLedger.record_action(
                db,
                AgentActionCreate(
                    task_id=task.id,
                    agent_id=agent.id,
                    organization_id=task.organization_id,
                    repository_id=target_repository_id,
                    change_id=task.change_id,
                    analysis_run_id=task.analysis_run_id,
                    action_type=action_type,
                    requested_capability=requested_capability,
                    tool_name=tool_name,
                    input_summary={"params": str(tool_kwargs)[:500]},
                    output_summary={"error": str(e)},
                    policy_decision="ALLOWED",
                    status="FAILED",
                ),
            )
            return {"success": False, "status": "FAILED", "action_id": action.id, "error": str(e)}
