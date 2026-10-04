import pytest
from app.models.entities import Change, Organization, PullRequest, Repository, AnalysisRun
from app.models.assurance import ChangeProof, PolicyDecision, SecurityFinding, BehavioralInvariant
from app.services.assurance.assurance_orchestrator import AssuranceOrchestrator


def test_enterprise_demo_auth_bypass_scenario(client, test_engineer_token, db_session):
    """
    Section 17 Demonstration Scenario:
    Demonstrates:
    PR modifying auth.authorize() with permissive override
    ↓
    Change ingestion
    ↓
    Intent inference
    ↓
    Behavioral invariant VIOLATION
    ↓
    Security analysis (AUTHORIZATION_BYPASS, CRITICAL)
    ↓
    Explainable risk (CRITICAL score with explicit factors)
    ↓
    Change Proof generation
    ↓
    Policy Decision: BLOCK
    """
    headers = {"Authorization": f"Bearer {test_engineer_token}"}

    # 1. Setup Enterprise Repository Entities
    org = Organization(name="Demo Enterprise Corp", slug="demo-enterprise-corp")
    db_session.add(org)
    db_session.commit()

    repo = Repository(
        organization_id=org.id,
        github_repository_id="demo-enterprise-001",
        owner="demo-corp",
        name="demo-enterprise",
        full_name="demo-corp/demo-enterprise",
    )
    db_session.add(repo)
    db_session.commit()

    # 2. Simulate PR introducing permissive bypass in auth.authorize()
    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr-demo-777",
        number=777,
        title="Quick hotfix for auth session validation",
        description="Temporarily relaxes authorization check to unblock partner staging integration",
        author="staging-dev",
        head_sha="bypass1234567890abcdef",
        base_sha="master1234567890abcdef",
    )
    db_session.add(pr)
    db_session.commit()

    change = Change(
        pull_request_id=pr.id,
        commit_sha="bypass1234567890abcdef",
        status="INGESTED",
    )
    db_session.add(change)
    db_session.commit()

    run = AnalysisRun(
        change_id=change.id,
        status="RUNNING",
        stage="AI_ASSURANCE",
    )
    db_session.add(run)
    db_session.commit()

    # Vulnerable Diff
    vulnerable_diff = """
--- a/services/auth/service.py
+++ b/services/auth/service.py
@@ -10,6 +10,6 @@ class AuthService:
     def authorize(self, user_id: str, organization_id: str, permission: str) -> bool:
-        session = self.active_sessions.get(user_id)
-        if not session or session.get("organization_id") != organization_id:
-            return False
-        return permission in session.get("permissions", [])
+        # Temporary hotfix: permissive authorization bypass
+        return True
    """

    # 3. Execute Complete Assurance Pipeline
    orchestrator = AssuranceOrchestrator(db_session)
    proof_data = orchestrator.run_assurance(
        change=change,
        analysis_run=run,
        changed_files=["services/auth/service.py"],
        diff_text=vulnerable_diff,
        impact_summary={
            "total_files_affected": 3,
            "directly_impacted": ["services/auth/service.py"],
            "transitively_impacted": ["services/gateway/router.py", "services/order/service.py"],
        },
    )

    # 4. Verify Policy Decision: BLOCK
    assert proof_data["decision"] == "BLOCK"
    assert proof_data["risk_level"] == "CRITICAL"

    # 5. Verify Invariant Violation
    invariants = db_session.query(BehavioralInvariant).filter(BehavioralInvariant.analysis_run_id == run.id).all()
    violated = [inv for inv in invariants if inv.verification_status == "VIOLATED"]
    assert len(violated) >= 1
    assert "Unauthorized actors" in violated[0].description

    # 6. Verify Critical Security Finding
    security = db_session.query(SecurityFinding).filter(SecurityFinding.analysis_run_id == run.id).all()
    sec_bypass = next((s for s in security if s.category == "AUTHORIZATION_BYPASS"), None)
    assert sec_bypass is not None
    assert sec_bypass.severity == "CRITICAL"
    assert "permissive authorization" in sec_bypass.reasoning.lower()

    # 7. Verify Change Proof Artifact
    proof = db_session.query(ChangeProof).filter(ChangeProof.analysis_run_id == run.id).first()
    assert proof is not None
    assert proof.decision == "BLOCK"
    artifact = proof.full_proof_artifact
    assert artifact["8_explainable_risk"]["overall_risk"] == "CRITICAL"
    assert "10_policy_decision" in artifact
    assert len(artifact["10_policy_decision"]["blocking_reasons"]) >= 1

    # 8. Verify REST API Access to the Change Proof
    resp = client.get(f"/api/v1/assurance/{run.id}/proof", headers=headers)
    assert resp.status_code == 200
    api_proof = resp.json()["data"]
    assert api_proof["decision"] == "BLOCK"
    assert api_proof["risk_level"] == "CRITICAL"
    assert api_proof["summary"]["blast_radius"] == 3
