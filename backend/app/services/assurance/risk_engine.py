"""
Explainable Risk Engine.

Combines deterministic structural metrics and semantic signals into an
explainable, traceable risk assessment with explicit contributing factors.
"""
from typing import Any, Dict, List, Optional, Tuple


class RiskEngine:
    """Computes explainable composite risk scores from aggregated change evidence."""

    @staticmethod
    def calculate_risk(
        changed_files: List[str],
        blast_radius: int = 1,
        security_findings: Optional[List[Dict[str, Any]]] = None,
        contracts: Optional[List[Dict[str, Any]]] = None,
        invariants: Optional[List[Dict[str, Any]]] = None,
        has_tests_modified: bool = False,
    ) -> Dict[str, Any]:
        """Aggregate evidence into an explainable risk assessment.

        Returns:
            Dict containing overall_risk, numerical_score, contributing_factors,
            confidence, and uncertainties.
        """
        factors: List[Dict[str, Any]] = []
        base_score = 15.0  # Base minimal change risk
        uncertainties: List[str] = []

        # 1. Component Criticality Factor
        is_auth_affected = any("auth" in f.lower() or "security" in f.lower() for f in changed_files)
        is_db_affected = any("model" in f.lower() or "alembic" in f.lower() for f in changed_files)

        if is_auth_affected:
            base_score += 30.0
            factors.append({
                "name": "CRITICAL_COMPONENT_AUTHENTICATION",
                "weight": 30.0,
                "description": "Authentication and authorization subsystems modified; high impact on system boundary security.",
                "evidence_ref": "auth_subsystem",
            })
        elif is_db_affected:
            base_score += 15.0
            factors.append({
                "name": "CRITICAL_COMPONENT_DATABASE",
                "weight": 15.0,
                "description": "Database schema or models modified; potential cascading persistence implications.",
                "evidence_ref": "database_subsystem",
            })

        # 2. Structural Blast Radius Factor
        if blast_radius > 10:
            base_score += 25.0
            factors.append({
                "name": "HIGH_BLAST_RADIUS",
                "weight": 25.0,
                "description": f"Transitive dependency graph shows {blast_radius} files impacted by change set.",
                "evidence_ref": f"blast_radius_{blast_radius}",
            })
        elif blast_radius > 3:
            base_score += 12.0
            factors.append({
                "name": "MODERATE_BLAST_RADIUS",
                "weight": 12.0,
                "description": f"Dependency graph traces impact across {blast_radius} files.",
                "evidence_ref": f"blast_radius_{blast_radius}",
            })

        # 3. Security Findings Factor
        if security_findings:
            critical_sec = [s for s in security_findings if s.get("severity") == "CRITICAL"]
            high_sec = [s for s in security_findings if s.get("severity") == "HIGH"]

            if critical_sec:
                base_score += 40.0
                factors.append({
                    "name": "CRITICAL_SECURITY_FINDINGS",
                    "weight": 40.0,
                    "description": f"{len(critical_sec)} critical security vulnerability signal(s) identified: {critical_sec[0].get('category')}.",
                    "evidence_ref": critical_sec[0].get("affected_component"),
                })
            elif high_sec:
                base_score += 20.0
                factors.append({
                    "name": "HIGH_SECURITY_FINDINGS",
                    "weight": 20.0,
                    "description": f"{len(high_sec)} high-severity security finding(s) detected.",
                    "evidence_ref": high_sec[0].get("affected_component"),
                })

        # 4. Semantic Contract Drift Factor
        if contracts:
            breaking = [c for c in contracts if c.get("classification") == "BREAKING"]
            potentially_breaking = [c for c in contracts if c.get("classification") == "POTENTIALLY_BREAKING"]

            if breaking:
                base_score += 35.0
                factors.append({
                    "name": "BREAKING_API_CONTRACT",
                    "weight": 35.0,
                    "description": f"Breaking API changes detected on endpoint {breaking[0].get('endpoint_path')}.",
                    "evidence_ref": breaking[0].get("endpoint_path"),
                })
            elif potentially_breaking:
                base_score += 15.0
                factors.append({
                    "name": "POTENTIALLY_BREAKING_CONTRACT",
                    "weight": 15.0,
                    "description": f"Potentially breaking contract drift detected on {potentially_breaking[0].get('endpoint_path')}.",
                    "evidence_ref": potentially_breaking[0].get("endpoint_path"),
                })

        # 5. Invariant Violations
        if invariants:
            violated = [inv for inv in invariants if inv.get("verification_status") == "VIOLATED"]
            if violated:
                base_score += 35.0
                factors.append({
                    "name": "INVARIANT_VIOLATION",
                    "weight": 35.0,
                    "description": f"Deterministic behavioral invariant violated: {violated[0].get('description')}.",
                    "evidence_ref": violated[0].get("affected_component"),
                })

        # 6. Test Coverage Signals
        if not has_tests_modified and (is_auth_affected or blast_radius > 3):
            base_score += 10.0
            factors.append({
                "name": "TEST_COVERAGE_GAP",
                "weight": 10.0,
                "description": "Significant functional change without accompanying new or modified test cases.",
                "evidence_ref": "test_suite",
            })
            uncertainties.append("Absence of regression test assertions on modified paths increases verification uncertainty.")

        # Cap score between 0.0 and 100.0
        final_score = min(100.0, max(0.0, base_score))

        # Overall risk level mapping
        if final_score >= 70.0:
            overall_risk = "CRITICAL"
        elif final_score >= 45.0:
            overall_risk = "HIGH"
        elif final_score >= 25.0:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        confidence = 0.95 if factors else 0.85

        return {
            "overall_risk": overall_risk,
            "numerical_score": round(final_score, 1),
            "contributing_factors": factors,
            "confidence": confidence,
            "uncertainties": uncertainties,
        }
