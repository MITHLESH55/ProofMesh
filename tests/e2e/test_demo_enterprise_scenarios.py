"""
End-to-end assurance test for the ProofMesh demo-enterprise seeded scenarios.

Guards the demo centerpiece: each of the seven controlled change scenarios must
produce the independently authored expected decision band when driven through
the real deterministic assurance engine + architecture policy layer.
"""
import os
import sys

import pytest

# Make the demo-enterprise package importable (its directory name is hyphenated,
# so it cannot be a normal package import — add it to sys.path directly).
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEMO_DIR = os.path.join(REPO_ROOT, "proofmesh-demo-enterprise")
if DEMO_DIR not in sys.path:
    sys.path.insert(0, DEMO_DIR)

from demo_assurance import run_all  # noqa: E402
from demo_scenarios import SCENARIOS  # noqa: E402

_RESULTS = {r["id"]: r for r in run_all()}


def test_all_seven_scenarios_present():
    assert len(SCENARIOS) == 7
    assert len(_RESULTS) == 7


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_scenario_matches_expected_decision(scenario):
    result = _RESULTS[scenario["id"]]
    assert result["final_decision"] == scenario["expected_decision"], (
        f"{scenario['id']}: decision {result['final_decision']} "
        f"!= expected {scenario['expected_decision']}"
    )
    assert result["final_risk"] == scenario["expected_risk"], (
        f"{scenario['id']}: risk {result['final_risk']} "
        f"!= expected {scenario['expected_risk']}"
    )


def test_forbidden_db_dependency_is_blocked_by_architecture_policy():
    """The forbidden cross-service DB access must trip policy AUTH-001."""
    result = _RESULTS["DEMO-2-FORBIDDEN-DB-DEP"]
    assert result["final_decision"] == "BLOCK"
    assert any(v["id"] == "AUTH-001" for v in result["arch_violations"])


def test_authorization_regression_violates_core_invariant():
    """The tenant-isolation regression must be caught by the core engine itself."""
    result = _RESULTS["DEMO-3-TENANT-ISOLATION-REGRESSION"]
    assert result["core_decision"] == "BLOCK"
    assert result["violated_invariants"]
    assert any(s["severity"] == "CRITICAL" for s in result["security_findings"])
