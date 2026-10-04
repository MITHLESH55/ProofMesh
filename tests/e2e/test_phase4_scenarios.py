"""
End-to-End Test Scenarios for Phase 4 — CI/CD & Runtime Assurance.

Verifies:
1. Scenario A: Healthy Deployment (PASS -> Allowed -> Runtime Verified)
2. Scenario B: Intentional Regression (Runtime Error Spike -> Runtime Regression Detected)
"""
import pytest
from app.models.entities import Organization, Repository, PullRequest, Change, AnalysisRun
from app.models.assurance import PolicyDecision, RiskAssessment
from app.services.assurance.assurance_orchestrator import AssuranceOrchestrator
from app.services.runtime.telemetry_service import TelemetryService
from app.services.runtime.runtime_assurance_engine import RuntimeAssuranceEngine
from app.services.runtime.github_check_service import GitHubCheckService
from app.schemas.runtime import (
    DeploymentCreate,
    RuntimeBaselineCreate,
    RuntimeObservationCreate,
    CIAssuranceCheckRequest,
)


@pytest.fixture
def enterprise_demo_setup(db_session):
    org = Organization(name="Enterprise Demo Corp", slug="enterprise-demo-corp")
    db_session.add(org)
    db_session.commit()

    repo = Repository(
        organization_id=org.id,
        github_repository_id="demo-repo-100",
        owner="enterprise-demo-corp",
        name="proofmesh-demo-enterprise",
        full_name="enterprise-demo-corp/proofmesh-demo-enterprise",
    )
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr-demo-1",
        number=101,
        title="Refactor auth.authorize() for zero-trust token claims",
        description="Updates JWT token claim extraction in auth service",
        author="lead-eng",
        head_sha="sha_auth_refactor_101",
        base_sha="sha_main_000",
    )
    db_session.add(pr)
    db_session.commit()

    change = Change(
        pull_request_id=pr.id,
        commit_sha="sha_auth_refactor_101",
        status="COMPLETED",
    )
    db_session.add(change)
    db_session.commit()

    run = AnalysisRun(
        change_id=change.id,
        status="COMPLETED",
        stage="AI_ASSURANCE",
    )
    db_session.add(run)
    db_session.commit()

    return {"org": org, "repo": repo, "pr": pr, "change": change, "run": run}


def test_e2e_healthy_deployment_scenario(client, test_engineer_token, db_session, enterprise_demo_setup):
    """
    Scenario A: Complete chain from Assurance -> CI Gate -> Deployment -> Healthy Telemetry -> Verified Change Proof.
    """
    headers = {"Authorization": f"Bearer {test_engineer_token}"}
    change = enterprise_demo_setup["change"]
    repo = enterprise_demo_setup["repo"]
    run = enterprise_demo_setup["run"]

    # 1. Run Phase 3 Assurance
    orch = AssuranceOrchestrator(db_session)
    proof_res = orch.run_assurance(change, run)
    assert proof_res["decision"] in ["PASS", "WARN"]

    # 2. Evaluate CI Gate
    ci_req = CIAssuranceCheckRequest(change_id=change.id, commit_sha=change.commit_sha)
    ci_res = GitHubCheckService.evaluate_ci_check(db_session, ci_req)
    assert ci_res.exit_code == 0
    assert "ProofMesh Assurance" in ci_res.policy_summary["markdown_summary"]

    # 3. Create Deployment in Staging
    dep = TelemetryService.create_deployment(
        db_session,
        DeploymentCreate(
            repository_id=repo.id,
            change_id=change.id,
            analysis_run_id=run.id,
            commit_sha=change.commit_sha,
            environment="staging",
            status="DEPLOYED",
        ),
    )

    # 4. Establish Pre-Deployment Baseline
    TelemetryService.record_baseline(
        db_session,
        RuntimeBaselineCreate(
            deployment_id=dep.id,
            service_name="auth-service",
            endpoint="/api/v1/auth/authorize",
            request_rate=50.0,
            error_rate=0.4,
            p50_latency_ms=28.0,
            p95_latency_ms=75.0,
            p99_latency_ms=130.0,
        ),
    )

    # 5. Ingest Healthy Post-Deployment Runtime Telemetry
    TelemetryService.record_observation(
        db_session,
        RuntimeObservationCreate(
            deployment_id=dep.id,
            service_name="auth-service",
            endpoint="/api/v1/auth/authorize",
            request_count=1200,
            error_count=4,
            error_rate=0.33,
            p50_latency_ms=27.0,
            p95_latency_ms=74.0,
            p99_latency_ms=128.0,
            status_2xx_count=1196,
            status_4xx_count=4,
            status_5xx_count=0,
        ),
    )

    # 6. Evaluate Runtime Assurance
    findings = RuntimeAssuranceEngine.evaluate_runtime_assurance(db_session, dep)
    runtime_decision = RuntimeAssuranceEngine.determine_runtime_decision(findings)
    assert runtime_decision == "RUNTIME_VERIFIED"
    assert any(f.finding_type == "RUNTIME_HEALTHY" for f in findings)

    # 7. Verify Extended Change Proof
    extended_proof = RuntimeAssuranceEngine.build_extended_change_proof(db_session, change.id, dep.id)
    assert extended_proof.runtime_decision == "RUNTIME_VERIFIED"
    assert extended_proof.final_combined_verdict == "VERIFIED_SAFE_IN_RUNTIME"
    assert extended_proof.runtime_evidence["total_requests_observed"] == 1200
    assert extended_proof.runtime_evidence["aggregate_error_rate_pct"] == 0.33


def test_e2e_regression_deployment_scenario(client, test_engineer_token, db_session, enterprise_demo_setup):
    """
    Scenario B: Deployment introduces material runtime regression -> ProofMesh catches it deterministically.
    """
    change = enterprise_demo_setup["change"]
    repo = enterprise_demo_setup["repo"]
    run = enterprise_demo_setup["run"]

    # 1. Run Phase 3 Assurance
    orch = AssuranceOrchestrator(db_session)
    orch.run_assurance(change, run)



    # 2. Create Deployment
    dep = TelemetryService.create_deployment(
        db_session,
        DeploymentCreate(
            repository_id=repo.id,
            change_id=change.id,
            analysis_run_id=run.id,
            commit_sha=change.commit_sha,
            environment="canary",
            status="CANARY",
        ),
    )

    # 3. Establish Baseline: 0.5% error rate, 70ms p95
    TelemetryService.record_baseline(
        db_session,
        RuntimeBaselineCreate(
            deployment_id=dep.id,
            service_name="auth-service",
            endpoint="/api/v1/auth/authorize",
            error_rate=0.5,
            p95_latency_ms=70.0,
        ),
    )

    # 4. Ingest Telemetry with Intentional Error Rate & Latency Regression
    TelemetryService.record_observation(
        db_session,
        RuntimeObservationCreate(
            deployment_id=dep.id,
            service_name="auth-service",
            endpoint="/api/v1/auth/authorize",
            request_count=1000,
            error_count=85,
            error_rate=8.5,
            p50_latency_ms=180.0,
            p95_latency_ms=520.0,
            p99_latency_ms=980.0,
            status_2xx_count=915,
            status_4xx_count=15,
            status_5xx_count=70,
        ),
    )

    # 5. Evaluate Runtime Assurance
    findings = RuntimeAssuranceEngine.evaluate_runtime_assurance(db_session, dep)
    runtime_decision = RuntimeAssuranceEngine.determine_runtime_decision(findings)
    assert runtime_decision == "RUNTIME_REGRESSION"

    finding_types = [f.finding_type for f in findings]
    assert "ERROR_RATE_REGRESSION" in finding_types
    assert "PERFORMANCE_REGRESSION" in finding_types
    assert "AVAILABILITY_REGRESSION" in finding_types

    # 6. Verify Extended Change Proof reflects regression
    extended_proof = RuntimeAssuranceEngine.build_extended_change_proof(db_session, change.id, dep.id)
    assert extended_proof.runtime_decision == "RUNTIME_REGRESSION"
    assert extended_proof.final_combined_verdict == "RUNTIME_REGRESSION_DETECTED"
    assert len(extended_proof.runtime_findings) >= 2
    assert "ERROR_RATE_REGRESSION" in extended_proof.runtime_evidence["regressions_detected"]
