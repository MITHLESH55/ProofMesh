"""
Change Proof Builder.

Assembles the formal, verifiable ProofMesh Change Proof artifact answering:
- WHAT CHANGED?
- WHY DID IT CHANGE?
- WHAT CAN IT AFFECT?
- WHAT BEHAVIOR MAY CHANGE?
- WHAT CONTRACTS MAY CHANGE?
- WHAT SECURITY PROPERTIES ARE AFFECTED?
- WHAT TESTS COVER IT?
- WHAT EVIDENCE SUPPORTS THE CONCLUSION?
- WHAT REMAINS UNCERTAIN?
- WHAT IS THE FINAL RISK?
- WHAT POLICY DECISION WAS MADE?
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ChangeProofBuilder:
    """Constructs formal verifiable Change Proof artifacts."""

    @staticmethod
    def build_proof(
        change_id: str,
        commit_sha: str,
        analysis_run_id: str,
        intent: Dict[str, Any],
        impact_summary: Dict[str, Any],
        invariants: List[Dict[str, Any]],
        contracts: List[Dict[str, Any]],
        security_findings: List[Dict[str, Any]],
        test_recommendations: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any],
        evidence_records: List[Dict[str, Any]],
        policy_decision: Dict[str, Any],
        pr_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compile complete formal Change Proof artifact."""
        now = datetime.now(timezone.utc).isoformat()

        # Summary for fast inspection
        summary = {
            "change_id": change_id,
            "commit_sha": commit_sha,
            "decision": policy_decision.get("decision", "PASS"),
            "risk_level": risk_assessment.get("overall_risk", "LOW"),
            "risk_score": risk_assessment.get("numerical_score", 0.0),
            "objective": intent.get("objective", "Code modification"),
            "category": intent.get("category", "FEATURE"),
            "files_changed_count": len(intent.get("affected_components", [])),
            "blast_radius": impact_summary.get("total_files_affected", 1),
            "critical_findings_count": sum(1 for s in security_findings if s.get("severity") == "CRITICAL"),
            "generated_at": now,
        }

        # Full structured proof artifact
        full_artifact = {
            "version": "1.0.0",
            "proof_metadata": {
                "change_id": change_id,
                "commit_sha": commit_sha,
                "analysis_run_id": analysis_run_id,
                "generated_at": now,
                "engine": "ProofMesh AI Assurance & Policy Decision Engine v0.3.0",
            },
            "pull_request": pr_metadata or {},
            "1_change_summary": {
                "commit_sha": commit_sha,
                "changed_files": intent.get("affected_components", []),
            },
            "2_intent": {
                "objective": intent.get("objective", ""),
                "category": intent.get("category", "FEATURE"),
                "affected_capability": intent.get("affected_capability", ""),
                "expected_behavior": intent.get("expected_behavior", ""),
                "confidence": intent.get("confidence", 0.9),
                "model_info": intent.get("model_info", {}),
            },
            "3_impact_and_blast_radius": {
                "changed_files_count": len(intent.get("affected_components", [])),
                "blast_radius_total": impact_summary.get("total_files_affected", 1),
                "directly_impacted": impact_summary.get("directly_impacted", []),
                "transitively_impacted": impact_summary.get("transitively_impacted", []),
            },
            "4_behavioral_invariants": {
                "total_invariants": len(invariants),
                "verified": [inv for inv in invariants if inv.get("verification_status") == "VERIFIED"],
                "violated": [inv for inv in invariants if inv.get("verification_status") == "VIOLATED"],
                "unverified": [inv for inv in invariants if inv.get("verification_status") == "UNVERIFIED"],
            },
            "5_semantic_contracts": {
                "total_contracts_analyzed": len(contracts),
                "breaking_contracts": [c for c in contracts if c.get("classification") == "BREAKING"],
                "potentially_breaking": [c for c in contracts if c.get("classification") == "POTENTIALLY_BREAKING"],
                "compatible_contracts": [c for c in contracts if c.get("classification") in ["COMPATIBLE_CHANGE", "NO_CHANGE"]],
            },
            "6_security_assurance": {
                "total_findings": len(security_findings),
                "critical": [s for s in security_findings if s.get("severity") == "CRITICAL"],
                "high": [s for s in security_findings if s.get("severity") == "HIGH"],
                "medium": [s for s in security_findings if s.get("severity") == "MEDIUM"],
                "low": [s for s in security_findings if s.get("severity") == "LOW"],
            },
            "7_test_coverage_and_recommendations": {
                "recommendations_count": len(test_recommendations),
                "recommended_tests": test_recommendations,
            },
            "8_explainable_risk": {
                "overall_risk": risk_assessment.get("overall_risk", "LOW"),
                "numerical_score": risk_assessment.get("numerical_score", 0.0),
                "contributing_factors": risk_assessment.get("contributing_factors", []),
                "confidence": risk_assessment.get("confidence", 0.9),
                "uncertainties": risk_assessment.get("uncertainties", []),
            },
            "9_evidence_ledger": {
                "total_evidence_units": len(evidence_records),
                "records": evidence_records,
            },
            "10_policy_decision": {
                "final_decision": policy_decision.get("decision", "PASS"),
                "blocking_reasons": policy_decision.get("blocking_reasons", []),
                "warning_reasons": policy_decision.get("warning_reasons", []),
                "rules_evaluated": policy_decision.get("rules_evaluated", []),
            },
        }

        return {
            "summary": summary,
            "full_proof_artifact": full_artifact,
            "decision": policy_decision.get("decision", "PASS"),
            "risk_level": risk_assessment.get("overall_risk", "LOW"),
        }
