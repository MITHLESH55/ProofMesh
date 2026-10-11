"""
ProofMesh Demo Enterprise — Assurance evaluation harness.

Drives each seeded scenario through the EXISTING deterministic assurance engine
(`backend/app/services/assurance`) and layers the demo's architecture/security
policy manifest on top, producing a combined PASS / WARN / BLOCK / RUNTIME_FINDING
decision. No core engine code is modified — this harness only orchestrates and
composes the engine's outputs, exactly as the platform's own orchestrator does.
"""
import os
import sys
from typing import Any, Dict, List, Optional

import yaml

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(ROOT_DIR, "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.assurance.contract_analyzer import ContractAnalyzer  # noqa: E402
from app.services.assurance.invariant_engine import InvariantEngine  # noqa: E402
from app.services.assurance.policy_engine import PolicyEngine  # noqa: E402
from app.services.assurance.risk_engine import RiskEngine  # noqa: E402
from app.services.assurance.security_analyzer import SecurityAnalyzer  # noqa: E402
from app.services.assurance.test_recommender import TestRecommender  # noqa: E402

POLICY_PATH = os.path.join(ROOT_DIR, "architecture", "policies.yaml")

_DECISION_RANK = {"PASS": 0, "WARN": 1, "BLOCK": 2}
_RISK_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
_RANK_RISK = {v: k for k, v in _RISK_RANK.items()}


def load_policies(path: str = POLICY_PATH) -> List[Dict[str, Any]]:
    """Load the architecture/security policy manifest."""
    with open(path, "r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    return manifest.get("policies", [])


def _service_of(file_path: str) -> Optional[str]:
    parts = file_path.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "services":
        return parts[1]
    return None
# __APPEND_ARCH__


def evaluate_architecture_policies(
    policies: List[Dict[str, Any]],
    changed_files: List[str],
    diff_text: str,
) -> List[Dict[str, Any]]:
    """Deterministically evaluate the policy manifest against a change.

    Returns a list of violations: {id, severity, description}.
    """
    violations: List[Dict[str, Any]] = []
    diff = diff_text.lower()
    services_changed = {_service_of(f) for f in changed_files if _service_of(f)}

    for policy in policies:
        rule = policy.get("rule")
        detect = policy.get("detect", {})
        hit = False

        if rule == "forbidden_db_access":
            sources = set(policy.get("source_services", []))
            if services_changed & sources:
                hit = any(sub.lower() in diff for sub in detect.get("any_substring", []))

        elif rule == "forbidden_public_admin_route":
            all_subs = [s.lower() for s in detect.get("all_substrings", [])]
            forbidden_absent = detect.get("and_not_substring", "").lower()
            if all_subs and all(s in diff for s in all_subs):
                hit = forbidden_absent not in diff

        elif rule == "forbidden_pii_sink":
            all_subs = [s.lower() for s in detect.get("all_substrings", [])]
            pii = [s.lower() for s in detect.get("pii_substrings", [])]
            if all_subs and all(s in diff for s in all_subs):
                hit = any(p in diff for p in pii)

        elif rule == "schema_change_requires_migration":
            model_subs = detect.get("model_file_substrings", [])
            mig_sub = detect.get("migration_path_substring", "migration")
            touches_schema = any(ms in f for f in changed_files for ms in model_subs)
            ships_migration = any(mig_sub in f.lower() for f in changed_files)
            hit = touches_schema and not ships_migration

        if hit:
            violations.append({
                "id": policy["id"],
                "severity": policy.get("severity", "high").lower(),
                "description": policy.get("description", "").strip(),
            })

    return violations


def _evaluate_runtime(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """Replicate the platform's deterministic runtime-regression thresholds."""
    reqs = telemetry.get("reqs", 0)
    if reqs == 0:
        return {"regression": True, "type": "INSUFFICIENT_RUNTIME_EVIDENCE", "risk": "HIGH"}

    base_err = telemetry.get("base_err", 0.5)
    obs_err = telemetry.get("obs_err", 0.0)
    base_p95 = telemetry.get("base_p95", 120.0)
    obs_p95 = telemetry.get("obs_p95", 0.0)

    if (obs_err > base_err * 2.5 and obs_err > 1.0) or obs_err > 2.0:
        return {"regression": True, "type": "ERROR_RATE_REGRESSION",
                "risk": "CRITICAL" if obs_err > 5.0 else "HIGH"}
    if obs_p95 > base_p95 * 1.75 or obs_p95 > 350.0:
        return {"regression": True, "type": "PERFORMANCE_REGRESSION",
                "risk": "HIGH" if obs_p95 > 500.0 else "MEDIUM"}
    return {"regression": False, "type": None, "risk": "LOW"}
# __APPEND_EVAL__


def evaluate_scenario(scenario: Dict[str, Any], policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run the full assurance pipeline (engine + policy layer) for one scenario."""
    changed_files = scenario["changed_files"]
    diff_text = scenario.get("diff_text", "")
    blast_radius = scenario.get("blast_radius", max(1, len(changed_files)))
    has_tests_modified = scenario.get("has_tests_modified", False)

    security = SecurityAnalyzer()
    contracts_engine = ContractAnalyzer()
    invariants_engine = InvariantEngine()
    test_recommender = TestRecommender()

    sec_findings = security.analyze_security(changed_files=changed_files, diff_text=diff_text)
    contracts = contracts_engine.analyze_contracts(changed_files=changed_files, diff_text=diff_text)
    invariants = invariants_engine.evaluate_invariants(changed_files=changed_files, diff_text=diff_text)
    risk = RiskEngine.calculate_risk(
        changed_files=changed_files,
        blast_radius=blast_radius,
        security_findings=sec_findings,
        contracts=contracts,
        invariants=invariants,
        has_tests_modified=has_tests_modified,
    )
    core_policy = PolicyEngine.evaluate(
        risk_assessment=risk,
        security_findings=sec_findings,
        contracts=contracts,
        invariants=invariants,
        evidence_count=len(changed_files),
    )
    recommended = test_recommender.generate_recommendations(
        changed_files=changed_files,
        title=scenario.get("title", ""),
        invariants=invariants,
        contracts=contracts,
        security_findings=sec_findings,
    )

    arch_violations = evaluate_architecture_policies(policies, changed_files, diff_text)
    arch_critical = any(v["severity"] == "critical" for v in arch_violations)
    arch_high = any(v["severity"] == "high" for v in arch_violations)

    # Runtime path takes precedence when live telemetry indicates a regression.
    runtime = None
    final_decision = core_policy["decision"]
    final_risk = risk["overall_risk"]

    if "telemetry" in scenario:
        runtime = _evaluate_runtime(scenario["telemetry"])
        if runtime["regression"]:
            final_decision = "RUNTIME_FINDING"
            final_risk = runtime["risk"]

    if final_decision != "RUNTIME_FINDING":
        arch_decision = "BLOCK" if arch_critical else ("WARN" if arch_high else "PASS")
        if _DECISION_RANK.get(arch_decision, 0) > _DECISION_RANK.get(final_decision, 0):
            final_decision = arch_decision
        if arch_critical:
            final_risk = "CRITICAL"
        elif arch_high and _RISK_RANK[final_risk] < _RISK_RANK["HIGH"]:
            final_risk = "HIGH"

    violated_invariants = [i for i in invariants if i.get("verification_status") == "VIOLATED"]

    expected_decision = scenario["expected_decision"]
    expected_risk = scenario["expected_risk"]
    passed = final_decision == expected_decision and final_risk == expected_risk

    return {
        "id": scenario["id"],
        "title": scenario["title"],
        "pdf_reference": scenario.get("pdf_reference", ""),
        "narrative": scenario.get("narrative", ""),
        "final_decision": final_decision,
        "final_risk": final_risk,
        "risk_score": risk["numerical_score"],
        "core_decision": core_policy["decision"],
        "core_risk": risk["overall_risk"],
        "security_findings": [{"category": s["category"], "severity": s["severity"]} for s in sec_findings],
        "contracts": [c["classification"] for c in contracts],
        "violated_invariants": [i["description"] for i in violated_invariants],
        "arch_violations": arch_violations,
        "runtime": runtime,
        "recommended_test_count": len(recommended),
        "blocking_reasons": core_policy["blocking_reasons"],
        "warning_reasons": core_policy["warning_reasons"],
        "expected_decision": expected_decision,
        "expected_risk": expected_risk,
        "passed": passed,
    }


def run_all() -> List[Dict[str, Any]]:
    """Evaluate every seeded scenario and return structured results."""
    from demo_scenarios import SCENARIOS

    policies = load_policies()
    return [evaluate_scenario(s, policies) for s in SCENARIOS]


