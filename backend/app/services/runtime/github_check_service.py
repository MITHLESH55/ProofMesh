"""
GitHub Status & CI Check Service.

Evaluates CI gate policy decisions, constructs developer-friendly GitHub Check Run
and commit status summaries, and records auditable CI gate check executions.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session

from app.models.runtime import CIAssuranceCheck
from app.models.assurance import ChangeProof, PolicyDecision, RiskAssessment, SecurityFinding, SemanticContract, TestRecommendation
from app.models.entities import Change
from app.schemas.runtime import CIAssuranceCheckRequest, CIAssuranceCheckResponse


class GitHubCheckService:
    """CI gate evaluation, exit code mapping, and GitHub status integration."""

    @classmethod
    def format_check_summary_markdown(
        cls,
        decision: str,
        risk_level: str,
        impact_count: int,
        critical_security_count: int,
        contract_status: str,
        test_gap_count: int,
        change_id: str,
        base_url: str = "http://localhost:3000",
    ) -> str:
        """Render standard markdown summary for GitHub Check Run / PR Comment."""
        proof_url = f"{base_url}/changes/{change_id}/assurance"
        status_emoji = {
            "PASS": "✅ PASS",
            "WARN": "⚠️ WARN",
            "BLOCK": "🚫 BLOCK",
            "INSUFFICIENT_EVIDENCE": "❓ INSUFFICIENT EVIDENCE",
        }.get(decision, decision)

        lines = [
            f"### ProofMesh Assurance — {status_emoji}",
            "",
            "| Metric | Assessment |",
            "| :--- | :--- |",
            f"| **Risk Level** | `{risk_level}` |",
            f"| **Impact Blast Radius** | `{impact_count} services / files` |",
            f"| **Critical Security Findings** | `{critical_security_count}` |",
            f"| **Contract Compatibility** | `{contract_status}` |",
            f"| **Test Coverage Gaps** | `{test_gap_count}` |",
            f"| **Gate Decision** | **`{decision}`** |",
            "",
            f"🔗 [View Formal Change Proof & Evidence in ProofMesh]({proof_url})",
        ]
        return "\n".join(lines)

    @classmethod
    def evaluate_ci_check(
        cls,
        db: Session,
        request: CIAssuranceCheckRequest,
        base_url: str = "http://localhost:3000",
    ) -> CIAssuranceCheckResponse:
        """
        Evaluate policy decision for a change, determine CI exit code, and record check run.
        """
        change = db.query(Change).filter(Change.id == request.change_id).first()
        commit_sha = request.commit_sha or (change.commit_sha if change else "HEAD")

        # Fetch Phase 3 Policy Decision and Proof
        policy = db.query(PolicyDecision).filter(PolicyDecision.change_id == request.change_id).order_by(PolicyDecision.created_at.desc()).first()
        risk = db.query(RiskAssessment).filter(RiskAssessment.change_id == request.change_id).order_by(RiskAssessment.created_at.desc()).first()
        security = db.query(SecurityFinding).filter(SecurityFinding.change_id == request.change_id).all()
        contracts = db.query(SemanticContract).filter(SemanticContract.change_id == request.change_id).all()
        tests = db.query(TestRecommendation).filter(TestRecommendation.change_id == request.change_id).all()

        if policy:
            gate_decision = policy.decision
            blocking_reasons = policy.blocking_reasons or []
            warning_reasons = policy.warning_reasons or []
            rules_evaluated = policy.rules_evaluated or []
        else:
            gate_decision = "INSUFFICIENT_EVIDENCE"
            blocking_reasons = ["No assurance analysis run completed for this change."]
            warning_reasons = []
            rules_evaluated = []

        risk_level = risk.overall_risk if risk else "UNKNOWN"
        crit_sec = sum(1 for s in security if s.severity == "CRITICAL")
        has_breaking_contract = any(c.classification == "BREAKING" for c in contracts)
        contract_status = "BREAKING" if has_breaking_contract else "COMPATIBLE"
        test_gap_count = len(tests)

        # Determine CI Exit Code
        if gate_decision == "BLOCK":
            exit_code = 1
        elif gate_decision == "WARN":
            exit_code = 2 if request.fail_on_warn else 0
        elif gate_decision == "PASS":
            exit_code = 0
        else:  # INSUFFICIENT_EVIDENCE
            exit_code = 3

        github_check_id = f"check_run_{uuid.uuid4().hex[:12]}" if request.publish_github_check else None

        policy_summary = {
            "gate_decision": gate_decision,
            "risk_level": risk_level,
            "exit_code": exit_code,
            "critical_security_count": crit_sec,
            "contract_status": contract_status,
            "test_gap_count": test_gap_count,
            "blocking_reasons": blocking_reasons,
            "warning_reasons": warning_reasons,
            "rules_evaluated": rules_evaluated,
            "markdown_summary": cls.format_check_summary_markdown(
                decision=gate_decision,
                risk_level=risk_level,
                impact_count=len(contracts) + 1,
                critical_security_count=crit_sec,
                contract_status=contract_status,
                test_gap_count=test_gap_count,
                change_id=request.change_id,
                base_url=base_url,
            ),
        }

        # Persist CI assurance check record
        ci_record = CIAssuranceCheck(
            change_id=request.change_id,
            commit_sha=commit_sha,
            gate_decision=gate_decision,
            policy_summary=policy_summary,
            exit_code=exit_code,
            github_check_id=github_check_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(ci_record)
        db.commit()
        db.refresh(ci_record)

        proof_url = f"{base_url}/changes/{request.change_id}/assurance"

        return CIAssuranceCheckResponse(
            id=ci_record.id,
            change_id=request.change_id,
            commit_sha=commit_sha,
            gate_decision=gate_decision,
            risk_level=risk_level,
            critical_findings=blocking_reasons,
            warning_findings=warning_reasons,
            policy_summary=policy_summary,
            exit_code=exit_code,
            github_check_id=github_check_id,
            proof_url=proof_url,
            created_at=ci_record.created_at,
        )
