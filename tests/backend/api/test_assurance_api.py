import pytest
from app.models.entities import Change, Organization, PullRequest, Repository, AnalysisRun
from app.models.assurance import (
    ChangeIntent,
    BehavioralInvariant,
    SemanticContract,
    SecurityFinding,
    TestRecommendation,
    RiskAssessment,
    EvidenceRecord,
    PolicyDecision,
    ChangeProof,
)


@pytest.fixture
def test_setup_entities(db_session, test_engineer_user):
    org = Organization(name="Test Org", slug="test-org")
    db_session.add(org)
    db_session.commit()

    repo = Repository(
        organization_id=org.id,
        github_repository_id="repo-999",
        owner="test-owner",
        name="test-repo",
        full_name="test-owner/test-repo",
    )
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr-101",
        number=42,
        title="Enhance security middleware",
        description="Adds authorization check to sensitive endpoints",
        author="engineer",
        head_sha="head12345678",
        base_sha="base12345678",
    )
    db_session.add(pr)
    db_session.commit()

    change = Change(
        pull_request_id=pr.id,
        commit_sha="head12345678",
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

    return {"org": org, "repo": repo, "pr": pr, "change": change, "run": run}


def test_assurance_analyze_endpoint(client, test_engineer_token, test_setup_entities):
    change = test_setup_entities["change"]
    headers = {"Authorization": f"Bearer {test_engineer_token}"}

    response = client.post(f"/api/v1/assurance/analyze/{change.id}", headers=headers)
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert res_data["change_id"] == change.id
    assert res_data["decision"] in ["PASS", "WARN", "BLOCK", "INSUFFICIENT_EVIDENCE"]
    assert "summary" in res_data
    assert "full_proof_artifact" in res_data


def test_assurance_overview_and_sub_endpoints(client, test_engineer_token, test_setup_entities, db_session):
    run = test_setup_entities["run"]
    change = test_setup_entities["change"]
    headers = {"Authorization": f"Bearer {test_engineer_token}"}

    # First analyze to populate DB
    client.post(f"/api/v1/assurance/analyze/{change.id}", headers=headers)

    # 1. Overview
    overview_resp = client.get(f"/api/v1/assurance/{run.id}", headers=headers)
    assert overview_resp.status_code == 200
    ov = overview_resp.json()["data"]
    assert ov["analysis_run_id"] == run.id
    assert ov["intent"] is not None
    assert len(ov["invariants"]) >= 1
    assert len(ov["evidence"]) >= 1
    assert ov["risk"] is not None
    assert ov["proof"] is not None

    # 2. Intent
    intent_resp = client.get(f"/api/v1/assurance/{run.id}/intent", headers=headers)
    assert intent_resp.status_code == 200
    assert intent_resp.json()["data"]["category"] in ["FEATURE", "SECURITY", "BUG_FIX"]

    # 3. Invariants
    inv_resp = client.get(f"/api/v1/assurance/{run.id}/invariants", headers=headers)
    assert inv_resp.status_code == 200
    assert len(inv_resp.json()["data"]) >= 1

    # 4. Contracts
    contracts_resp = client.get(f"/api/v1/assurance/{run.id}/contracts", headers=headers)
    assert contracts_resp.status_code == 200

    # 5. Security
    sec_resp = client.get(f"/api/v1/assurance/{run.id}/security", headers=headers)
    assert sec_resp.status_code == 200

    # 6. Risk
    risk_resp = client.get(f"/api/v1/assurance/{run.id}/risk", headers=headers)
    assert risk_resp.status_code == 200
    assert risk_resp.json()["data"]["overall_risk"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # 7. Evidence
    ev_resp = client.get(f"/api/v1/assurance/{run.id}/evidence", headers=headers)
    assert ev_resp.status_code == 200
    assert len(ev_resp.json()["data"]) >= 1

    # 8. Proof
    proof_resp = client.get(f"/api/v1/assurance/{run.id}/proof", headers=headers)
    assert proof_resp.status_code == 200
    assert proof_resp.json()["data"]["decision"] in ["PASS", "WARN", "BLOCK", "INSUFFICIENT_EVIDENCE"]

    # 9. Reevaluate Decision
    decision_resp = client.post(
        f"/api/v1/assurance/{run.id}/decision",
        json={"policy_overrides": {}},
        headers=headers,
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["data"]["decision"] in ["PASS", "WARN", "BLOCK", "INSUFFICIENT_EVIDENCE"]
