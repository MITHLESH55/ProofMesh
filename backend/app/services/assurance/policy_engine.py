"""
Deterministic Policy Decision Engine.

Evaluates evidence, risk scores, security findings, and invariants against
configurable policy rules to reach an objective governance decision:
PASS, WARN, BLOCK, or INSUFFICIENT_EVIDENCE.
"""
from typing import Any, Dict, List, Optional


class PolicyEngine:
    """Evaluates software changes against deterministic governance policies."""

    @staticmethod
    def evaluate(
        risk_assessment: Dict[str, Any],
        security_findings: Optional[List[Dict[str, Any]]] = None,
        contracts: Optional[List[Dict[str, Any]]] = None,
        invariants: Optional[List[Dict[str, Any]]] = None,
        evidence_count: int = 0,
        policy_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluate change assurance signals against policy rules.

        Returns:
            Dict containing decision (PASS/WARN/BLOCK/INSUFFICIENT_EVIDENCE),
            rules_evaluated, blocking_reasons, and warning_reasons.
        """
        blocking_reasons: List[str] = []
        warning_reasons: List[str] = []
        rules_evaluated: List[Dict[str, Any]] = []

        # 1. Rule: Insufficient Evidence Check
        # If no evidence or very high uncertainty, policy must state INSUFFICIENT_EVIDENCE
        if evidence_count == 0 and not security_findings and not contracts:
            rules_evaluated.append({
                "rule_id": "POL_001_EVIDENCE_SUFFICIENCY",
                "name": "Evidence Sufficiency",
                "result": "FAILED",
                "description": "Requires minimum verifiable evidence before rendering a pass/warn decision.",
            })
            return {
                "decision": "INSUFFICIENT_EVIDENCE",
                "rules_evaluated": rules_evaluated,
                "blocking_reasons": ["No verifiable code diff, graph relation, or AST fact was supplied for analysis."],
                "warning_reasons": [],
            }
        else:
            rules_evaluated.append({
                "rule_id": "POL_001_EVIDENCE_SUFFICIENCY",
                "name": "Evidence Sufficiency",
                "result": "PASSED",
                "description": f"Verified {evidence_count} evidence records present.",
            })

        # 2. Rule: Critical Security Vulnerability Block
        critical_security = [s for s in (security_findings or []) if s.get("severity") == "CRITICAL"]
        if critical_security:
            reason = f"Critical security issue detected: {critical_security[0].get('category')} ({critical_security[0].get('reasoning')})"
            blocking_reasons.append(reason)
            rules_evaluated.append({
                "rule_id": "POL_002_NO_CRITICAL_SECURITY",
                "name": "Zero Critical Vulnerabilities",
                "result": "FAILED",
                "details": reason,
            })
        else:
            rules_evaluated.append({
                "rule_id": "POL_002_NO_CRITICAL_SECURITY",
                "name": "Zero Critical Vulnerabilities",
                "result": "PASSED",
            })

        # 3. Rule: Invariant Violation Block
        violated_invariants = [inv for inv in (invariants or []) if inv.get("verification_status") == "VIOLATED"]
        if violated_invariants:
            reason = f"Behavioral invariant violated: {violated_invariants[0].get('description')}"
            blocking_reasons.append(reason)
            rules_evaluated.append({
                "rule_id": "POL_003_BEHAVIORAL_INVARIANTS",
                "name": "Behavioral Invariants Preserved",
                "result": "FAILED",
                "details": reason,
            })
        else:
            rules_evaluated.append({
                "rule_id": "POL_003_BEHAVIORAL_INVARIANTS",
                "name": "Behavioral Invariants Preserved",
                "result": "PASSED",
            })

        # 4. Rule: Breaking API Contract Check
        breaking_contracts = [c for c in (contracts or []) if c.get("classification") == "BREAKING"]
        if breaking_contracts:
            reason = f"Breaking contract change on {breaking_contracts[0].get('endpoint_path')} requires explicit migration."
            blocking_reasons.append(reason)
            rules_evaluated.append({
                "rule_id": "POL_004_API_CONTRACT_COMPATIBILITY",
                "name": "API Contract Compatibility",
                "result": "FAILED",
                "details": reason,
            })
        else:
            rules_evaluated.append({
                "rule_id": "POL_004_API_CONTRACT_COMPATIBILITY",
                "name": "API Contract Compatibility",
                "result": "PASSED",
            })

        # 5. Rule: High Risk / High Severity Warnings
        high_security = [s for s in (security_findings or []) if s.get("severity") == "HIGH"]
        potentially_breaking = [c for c in (contracts or []) if c.get("classification") == "POTENTIALLY_BREAKING"]
        overall_risk = risk_assessment.get("overall_risk", "LOW")

        if high_security:
            warning_reasons.append(f"High-severity security finding: {high_security[0].get('category')}")
        if potentially_breaking:
            warning_reasons.append(f"Potentially breaking contract drift on {potentially_breaking[0].get('endpoint_path')}")
        if overall_risk == "HIGH" and not blocking_reasons:
            warning_reasons.append(f"Elevated risk score ({risk_assessment.get('numerical_score')}) requires peer architectural review.")

        # Determine Final Decision
        if blocking_reasons:
            decision = "BLOCK"
        elif warning_reasons:
            decision = "WARN"
        else:
            decision = "PASS"

        return {
            "decision": decision,
            "rules_evaluated": rules_evaluated,
            "blocking_reasons": blocking_reasons,
            "warning_reasons": warning_reasons,
        }
