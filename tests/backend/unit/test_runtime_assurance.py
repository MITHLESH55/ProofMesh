"""
Unit tests for Phase 4 Runtime Assurance — Telemetry, Prediction Matching, Regression Detection & CI Gates.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.entities import Organization, Repository, PullRequest, Change, User, UserRole
from app.models.runtime import Deployment, RuntimeBaseline, RuntimeObservation, RuntimeFinding
from app.models.assurance import ChangeIntent, ChangeProof, PolicyDecision, RiskAssessment
from app.schemas.runtime import (
    DeploymentCreate,
    RuntimeBaselineCreate,
    RuntimeObservationCreate,
    CIAssuranceCheckRequest,
)
from app.services.runtime.telemetry_service import TelemetryService
from app.services.runtime.prediction_matcher import PredictionMatcher
from app.services.runtime.runtime_assurance_engine import RuntimeAssuranceEngine
from app.services.runtime.github_check_service import GitHubCheckService


@pytest.fixture
def test_setup_entities(db_session: Session):
    """Setup test organization, repository, change and deployment."""
    org = Organization(name="Test Corp", slug="test-corp")
    db_session.add(org)
    db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repository_id="99999",
        owner="test-org",
        name="core-service",
        full_name="test-org/core-service",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()


    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="101",
        number=1,
        title="Refactor auth.authorize()",
        author="eng1",
        head_sha="sha_auth_1234",
        base_sha="sha_base_0000",
        state="OPEN",
    )
    db_session.add(pr)
    db_session.flush()

    change = Change(pull_request_id=pr.id, commit_sha="sha_auth_1234", status="COMPLETED", source="GITHUB_PR")
    db_session.add(change)
    db_session.flush()

    intent = ChangeIntent(
        change_id=change.id,
        analysis_run_id="run_1",
        objective="Update authentication token validation",
        category="SECURITY_FIX",
        affected_capability="Authentication",
        affected_components=["auth-service", "user-service"],
        confidence=0.95,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(intent)
    db_session.flush()

    dep = Deployment(
        repository_id=repo.id,
        change_id=change.id,
        analysis_run_id="run_1",
        commit_sha="sha_auth_1234",
        environment="staging",
        status="DEPLOYED",
        deployed_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(dep)
    db_session.commit()

    return {
        "org": org,
        "repo": repo,
        "pr": pr,
        "change": change,
        "deployment": dep,
    }


def test_telemetry_service_crud_and_metrics(db_session: Session, test_setup_entities):
    dep = test_setup_entities["deployment"]

    # 1. Record Baseline
    base_data = RuntimeBaselineCreate(
        deployment_id=dep.id,
        service_name="auth-service",
        endpoint="/api/v1/auth/login",
        request_rate=25.0,
        error_rate=0.5,
        p50_latency_ms=30.0,
        p95_latency_ms=90.0,
        p99_latency_ms=180.0,
        sample_window_seconds=300,
    )
    baseline = TelemetryService.record_baseline(db_session, base_data)
    assert baseline.id is not None
    assert baseline.service_name == "auth-service"

    # 2. Record Observation
    obs_data = RuntimeObservationCreate(
        deployment_id=dep.id,
        service_name="auth-service",
        endpoint="/api/v1/auth/login",
        request_count=1000,
        error_count=5,
        error_rate=0.5,
        p50_latency_ms=32.0,
        p95_latency_ms=92.0,
        p99_latency_ms=185.0,
        status_2xx_count=995,
        status_4xx_count=5,
        status_5xx_count=0,
    )
    observation = TelemetryService.record_observation(db_session, obs_data)
    assert observation.id is not None
    assert observation.request_count == 1000

    # 3. Query Metrics Summary
    summary = TelemetryService.get_metrics_summary(db_session, deployment_id=dep.id)
    assert summary.total_requests == 1000
    assert summary.total_errors == 5
    assert summary.overall_error_rate == 0.5
    assert len(summary.services) == 1
    assert summary.services[0].status == "HEALTHY"

    # 4. Generate Prometheus Metrics text
    prom_text = TelemetryService.generate_prometheus_metrics(db_session)
    assert "proofmesh_http_requests_total" in prom_text
    assert 'service="auth-service"' in prom_text
    assert "proofmesh_service_error_rate" in prom_text


def test_prediction_matcher(db_session: Session, test_setup_entities):
    dep = test_setup_entities["deployment"]

    # Record observation for auth-service (predicted) and unexpected-service
    TelemetryService.record_observation(
        db_session,
        RuntimeObservationCreate(
            deployment_id=dep.id,
            service_name="auth-service",
            endpoint="/api/v1/auth",
            request_count=400,
            error_count=2,
            error_rate=0.5,
            p95_latency_ms=80.0,
        ),
    )
    TelemetryService.record_observation(
        db_session,
        RuntimeObservationCreate(
            deployment_id=dep.id,
            service_name="billing-service",
            endpoint="/api/v1/billing",
            request_count=200,
            error_count=0,
            error_rate=0.0,
            p95_latency_ms=50.0,
        ),
    )

    report = PredictionMatcher.compare_prediction_vs_observed(
        db_session, dep, predicted_services=["auth-service", "user-service"]
    )

    comp_map = {c.service_name: c for c in report.components}
    assert comp_map["auth-service"].status == "MATCH"
    assert comp_map["user-service"].status == "UNEXPECTED_QUIET"
    assert comp_map["billing-service"].status == "UNEXPECTED_TRAFFIC"


def test_runtime_assurance_regression_detection(db_session: Session, test_setup_entities):
    dep = test_setup_entities["deployment"]

    # Baseline: 0.5% error rate, 80ms p95
    TelemetryService.record_baseline(
        db_session,
        RuntimeBaselineCreate(
            deployment_id=dep.id,
            service_name="auth-service",
            endpoint="/api/v1/auth/authorize",
            error_rate=0.5,
            p95_latency_ms=80.0,
        ),
    )

    # Observation with high regression: 8.5% error rate, 450ms p95 latency, 40 5xx errors
    TelemetryService.record_observation(
        db_session,
        RuntimeObservationCreate(
            deployment_id=dep.id,
            service_name="auth-service",
            endpoint="/api/v1/auth/authorize",
            request_count=500,
            error_count=42,
            error_rate=8.4,
            p95_latency_ms=450.0,
            status_2xx_count=458,
            status_4xx_count=12,
            status_5xx_count=30,
        ),
    )

    findings = RuntimeAssuranceEngine.evaluate_runtime_assurance(db_session, dep)
    assert len(findings) >= 2

    finding_types = [f.finding_type for f in findings]
    assert "ERROR_RATE_REGRESSION" in finding_types
    assert "PERFORMANCE_REGRESSION" in finding_types
    assert "AVAILABILITY_REGRESSION" in finding_types

    decision = RuntimeAssuranceEngine.determine_runtime_decision(findings)
    assert decision == "RUNTIME_REGRESSION"


def test_github_check_service_and_ci_exit_codes(db_session: Session, test_setup_entities):
    change = test_setup_entities["change"]

    # Setup Phase 3 Policy Decision as BLOCK
    policy = PolicyDecision(
        change_id=change.id,
        analysis_run_id="run_1",
        decision="BLOCK",
        blocking_reasons=["Critical authorization bypass risk detected in auth.authorize()"],
        warning_reasons=[],
        rules_evaluated=[{"rule": "require_zero_critical_security", "passed": False}],
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(policy)
    db_session.commit()

    # Evaluate CI gate
    req = CIAssuranceCheckRequest(
        change_id=change.id,
        commit_sha=change.commit_sha,
        fail_on_warn=False,
        publish_github_check=True,
    )
    ci_res = GitHubCheckService.evaluate_ci_check(db_session, req)

    assert ci_res.gate_decision == "BLOCK"
    assert ci_res.exit_code == 1
    assert "Critical authorization bypass" in ci_res.critical_findings[0]
    assert ci_res.github_check_id is not None
    assert "ProofMesh Assurance — 🚫 BLOCK" in ci_res.policy_summary["markdown_summary"]

