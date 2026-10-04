"""
API tests for Phase 4 Deployments, Runtime Telemetry, Findings, Extended Change Proofs & CI Gates.
"""
import pytest
from app.models.entities import Change, Organization, PullRequest, Repository, AnalysisRun


@pytest.fixture
def runtime_test_entities(db_session):
    org = Organization(name="Observability Org", slug="obs-org")
    db_session.add(org)
    db_session.commit()

    repo = Repository(
        organization_id=org.id,
        github_repository_id="repo-888",
        owner="obs-org",
        name="gateway-service",
        full_name="obs-org/gateway-service",
    )
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr-202",
        number=15,
        title="Deploy auth optimization",
        description="Improves token caching and session verification",
        author="eng2",
        head_sha="sha_deploy_8888",
        base_sha="sha_base_8888",
    )
    db_session.add(pr)
    db_session.commit()

    change = Change(
        pull_request_id=pr.id,
        commit_sha="sha_deploy_8888",
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


def test_deployment_lifecycle_and_runtime_api(client, test_engineer_token, runtime_test_entities):
    headers = {"Authorization": f"Bearer {test_engineer_token}"}
    repo = runtime_test_entities["repo"]
    change = runtime_test_entities["change"]
    run = runtime_test_entities["run"]

    # 1. Create Deployment
    create_payload = {
        "repository_id": repo.id,
        "change_id": change.id,
        "analysis_run_id": run.id,
        "commit_sha": change.commit_sha,
        "environment": "staging",
        "status": "DEPLOYED",
    }
    dep_resp = client.post("/api/v1/deployments", json=create_payload, headers=headers)
    assert dep_resp.status_code == 201
    dep_data = dep_resp.json()["data"]
    deployment_id = dep_data["id"]
    assert dep_data["environment"] == "staging"
    assert dep_data["status"] == "DEPLOYED"

    # 2. List Deployments
    list_resp = client.get("/api/v1/deployments", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    # 3. Get Deployment by ID
    get_resp = client.get(f"/api/v1/deployments/{deployment_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == deployment_id

    # 4. Record Baseline
    base_payload = {
        "deployment_id": deployment_id,
        "service_name": "gateway-service",
        "endpoint": "/api/v1/gateway",
        "request_rate": 30.0,
        "error_rate": 0.3,
        "p50_latency_ms": 25.0,
        "p95_latency_ms": 70.0,
        "p99_latency_ms": 150.0,
        "sample_window_seconds": 300,
    }
    base_resp = client.post(f"/api/v1/deployments/{deployment_id}/baselines", json=base_payload, headers=headers)
    assert base_resp.status_code == 201

    # 5. Record Observation
    obs_payload = {
        "deployment_id": deployment_id,
        "service_name": "gateway-service",
        "endpoint": "/api/v1/gateway",
        "request_count": 800,
        "error_count": 2,
        "error_rate": 0.25,
        "p50_latency_ms": 26.0,
        "p95_latency_ms": 72.0,
        "p99_latency_ms": 155.0,
        "status_2xx_count": 798,
        "status_4xx_count": 2,
        "status_5xx_count": 0,
    }
    obs_resp = client.post(f"/api/v1/deployments/{deployment_id}/observations", json=obs_payload, headers=headers)
    assert obs_resp.status_code == 201

    # 6. Query Deployment Runtime Telemetry
    runtime_resp = client.get(f"/api/v1/deployments/{deployment_id}/runtime", headers=headers)
    assert runtime_resp.status_code == 200
    rdata = runtime_resp.json()["data"]
    assert len(rdata["baselines"]) == 1
    assert len(rdata["observations"]) == 1

    # 7. Query Deployment Assurance
    assurance_resp = client.get(f"/api/v1/deployments/{deployment_id}/assurance", headers=headers)
    assert assurance_resp.status_code == 200
    ass_data = assurance_resp.json()["data"]
    assert ass_data["runtime_decision"] == "RUNTIME_VERIFIED"
    assert len(ass_data["findings"]) >= 1

    # 8. Query Global Runtime Services & Metrics
    services_resp = client.get("/api/v1/runtime/services", headers=headers)
    assert services_resp.status_code == 200
    assert len(services_resp.json()["data"]) >= 1

    metrics_resp = client.get("/api/v1/runtime/metrics", headers=headers)
    assert metrics_resp.status_code == 200
    assert metrics_resp.json()["data"]["total_requests"] == 800

    # 9. Extended Change Proof
    proof_resp = client.get(f"/api/v1/changes/{change.id}/runtime", headers=headers)
    assert proof_resp.status_code == 200
    proof_data = proof_resp.json()["data"]
    assert proof_data["runtime_decision"] == "RUNTIME_VERIFIED"
    assert proof_data["final_combined_verdict"] == "VERIFIED_SAFE_IN_RUNTIME"

    # 10. Prometheus Scrape Endpoint
    prom_resp = client.get("/metrics")
    assert prom_resp.status_code == 200
    assert "proofmesh_http_requests_total" in prom_resp.text


def test_ci_check_endpoint(client, test_engineer_token, runtime_test_entities):
    headers = {"Authorization": f"Bearer {test_engineer_token}"}
    change = runtime_test_entities["change"]

    ci_payload = {
        "change_id": change.id,
        "commit_sha": change.commit_sha,
        "fail_on_warn": False,
        "publish_github_check": True,
    }
    ci_resp = client.post("/api/v1/ci/check", json=ci_payload, headers=headers)
    assert ci_resp.status_code == 200
    data = ci_resp.json()["data"]
    assert "gate_decision" in data
    assert "exit_code" in data
    assert "proof_url" in data
    assert "markdown_summary" in data["policy_summary"]
