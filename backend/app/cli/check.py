"""
ProofMesh CI Check CLI.

Usage:
    python -m app.cli.check <change_id> [--fail-on-warn] [--json] [--base-url http://localhost:3000]

Evaluates ProofMesh policy decision for a pull request change, outputs machine-readable
and human-readable summaries, and exits with appropriate process exit codes:
    0: PASS (or WARN when --fail-on-warn is not set)
    1: BLOCK (Policy blocked due to critical risk / violations)
    2: WARN (when --fail-on-warn is set)
    3: INSUFFICIENT_EVIDENCE or system error
"""
import argparse
import json
import sys

from app.db.session import SessionLocal
from app.schemas.runtime import CIAssuranceCheckRequest
from app.services.runtime.github_check_service import GitHubCheckService


def main() -> int:
    parser = argparse.ArgumentParser(description="ProofMesh CI/CD Assurance Gate CLI")
    parser.add_argument("change_id", type=str, help="UUID or identifier of the Change under test")
    parser.add_argument("--commit-sha", type=str, default=None, help="Commit SHA associated with the check")
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit with non-zero code if decision is WARN")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output machine-readable JSON")
    parser.add_argument("--base-url", type=str, default="http://localhost:3000", help="Base URL for ProofMesh links")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        req = CIAssuranceCheckRequest(
            change_id=args.change_id,
            commit_sha=args.commit_sha,
            fail_on_warn=args.fail_on_warn,
            publish_github_check=True,
        )
        result = GitHubCheckService.evaluate_ci_check(db, req, base_url=args.base_url)

        if args.json_output:
            print(json.dumps(result.model_dump(), default=str, indent=2))
        else:
            print("==================================================")
            print("         ProofMesh CI Assurance Gate Result       ")
            print("==================================================")
            print(f"Change ID:        {result.change_id}")
            print(f"Commit SHA:       {result.commit_sha}")
            print(f"Gate Decision:    {result.gate_decision}")
            print(f"Risk Level:       {result.risk_level}")
            print(f"Exit Code:        {result.exit_code}")
            print(f"Proof URL:        {result.proof_url}")
            print("--------------------------------------------------")
            if result.critical_findings:
                print("Critical / Blocking Reasons:")
                for r in result.critical_findings:
                    print(f"  - {r}")
            if result.warning_findings:
                print("Warnings:")
                for w in result.warning_findings:
                    print(f"  - {w}")
            print("==================================================")

        return result.exit_code

    except Exception as e:
        if args.json_output:
            print(json.dumps({"error": str(e), "exit_code": 3}))
        else:
            print(f"[ERROR] Failed to evaluate CI check: {e}", file=sys.stderr)
        return 3
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
