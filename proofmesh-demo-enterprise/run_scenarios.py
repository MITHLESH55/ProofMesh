"""
ProofMesh Demo Enterprise — Seeded Scenario Runner (demo centerpiece).

Runs the seven controlled change scenarios through the deterministic assurance
engine + architecture policy layer and prints a Change-Proof-style decision
table. Exits non-zero if any scenario deviates from its independently authored
expected decision band, so the demo is CI-verifiable, not just illustrative.

Usage:
    python proofmesh-demo-enterprise/run_scenarios.py          # summary table
    python proofmesh-demo-enterprise/run_scenarios.py -v       # full change proofs
"""
import argparse
import os
import sys

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from demo_assurance import run_all  # noqa: E402

_DECISION_GLYPH = {
    "PASS": "PASS   ",
    "WARN": "REVIEW ",
    "BLOCK": "BLOCK  ",
    "RUNTIME_FINDING": "RUNTIME",
}


def _print_change_proof(result: dict) -> None:
    print("=" * 78)
    print(f"CHANGE PROOF — {result['id']}")
    print(f"  {result['title']}")
    print("-" * 78)
    print(f"  Narrative      : {result['narrative']}")
    print(f"  Decision       : {result['final_decision']}  (risk {result['final_risk']}, "
          f"score {result['risk_score']})")
    if result["security_findings"]:
        for s in result["security_findings"]:
            print(f"  Security       : {s['severity']:8} {s['category']}")
    if result["violated_invariants"]:
        for inv in result["violated_invariants"]:
            print(f"  Invariant      : VIOLATED  {inv}")
    if any(c in ("BREAKING", "POTENTIALLY_BREAKING") for c in result["contracts"]):
        print(f"  Contract drift : {', '.join(result['contracts'])}")
    for v in result["arch_violations"]:
        print(f"  Arch policy    : {v['severity'].upper():8} {v['id']} — {v['description']}")
    if result["runtime"] and result["runtime"]["regression"]:
        print(f"  Runtime        : {result['runtime']['type']}")
    print(f"  Tests advised  : {result['recommended_test_count']}")
    print(f"  Expected       : {result['expected_decision']} / {result['expected_risk']}  "
          f"-> {'MATCH' if result['passed'] else 'MISMATCH'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="ProofMesh demo-enterprise scenario runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="print full change proofs")
    args = parser.parse_args()

    results = run_all()

    if args.verbose:
        for result in results:
            _print_change_proof(result)
        print("=" * 78)

    print()
    print("PROOFMESH DEMO ENTERPRISE — SEEDED SCENARIO ASSURANCE")
    print("=" * 78)
    print(f"{'SCENARIO':<34}{'DECISION':<10}{'RISK':<10}{'EXPECTED':<12}{'RESULT'}")
    print("-" * 78)
    for r in results:
        expected = f"{r['expected_decision']}/{r['expected_risk']}"
        status = "ok" if r["passed"] else "FAIL"
        print(f"{r['id']:<34}{_DECISION_GLYPH.get(r['final_decision'], r['final_decision']):<10}"
              f"{r['final_risk']:<10}{expected:<12}{status}")
    print("-" * 78)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"{passed}/{total} scenarios matched their expected assurance decision.")
    print("=" * 78)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
