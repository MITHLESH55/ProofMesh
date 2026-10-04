import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.workers.worker import AnalysisWorker


def generate_signature(body: bytes, secret: str = settings.GITHUB_WEBHOOK_SECRET) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def test_primary_phase1_flow(client: TestClient, db_session, test_admin_token: str):
    """
    Complete Phase 1 Primary Flow Verification:
    1. GitHub sends pull_request.opened webhook.
    2. ProofMesh API validates HMAC signature & ingests event.
    3. Repository, PullRequest, and Change entities are persisted in DB.
    4. AnalysisRun is created with QUEUED status.
    5. Background AnalysisWorker picks up and processes the job.
    6. AnalysisRun transitions QUEUED -> RUNNING -> COMPLETED.
    7. Change status updates to COMPLETED.
    8. Audit logs are recorded throughout the pipeline.
    9. Change detail & status APIs return full persisted state for UI consumption.
    """
    # Step 1: Simulate GitHub PR Webhook Payload
    pr_number = 42
    commit_sha = "8af932ce91d4e680a719d3fbc91c14d952674e12"
    webhook_payload = {
        "action": "opened",
        "number": pr_number,
        "repository": {
            "id": 987654321,
            "name": "demo-enterprise",
            "full_name": "proofmesh-demo-org/demo-enterprise",
            "owner": {"login": "proofmesh-demo-org", "id": 500},
            "default_branch": "main",
        },
        "pull_request": {
            "id": 1234567,
            "number": pr_number,
            "title": "Add organization profile endpoint",
            "body": "Implements tenant settings and organization profile endpoints for Phase 1.",
            "user": {"login": "octocat", "id": 1},
            "head": {"sha": commit_sha},
            "base": {"sha": "1111111111111111111111111111111111111111"},
            "state": "open",
        },
    }
    raw_body = json.dumps(webhook_payload).encode("utf-8")
    signature = generate_signature(raw_body)
    delivery_id = "delivery-e2e-phase1-primary-flow"

    # Step 2: Ingest via POST /api/v1/webhooks/github
    webhook_resp = client.post(
        "/api/v1/webhooks/github",
        content=raw_body,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": delivery_id,
            "Content-Type": "application/json",
        },
    )
    assert webhook_resp.status_code == 200
    webhook_data = webhook_resp.json()["data"]

    change_id = webhook_data["change_id"]
    analysis_run_id = webhook_data["analysis_run_id"]
    assert webhook_data["status"] == "queued"
    assert webhook_data["commit_sha"] == commit_sha

    # Step 3: Verify Change is currently QUEUED via API
    headers = {"Authorization": f"Bearer {test_admin_token}"}
    status_resp_1 = client.get(f"/api/v1/changes/{change_id}/status", headers=headers)
    assert status_resp_1.status_code == 200
    assert status_resp_1.json()["data"]["status"] == "QUEUED"

    # Step 4: Worker processes the queued job
    worker = AnalysisWorker(worker_id="worker-e2e-test")
    job_payload = {
        "change_id": change_id,
        "analysis_run_id": analysis_run_id,
        "attempt": 1,
        "max_attempts": 3,
    }
    success = worker.process_job(job_payload, db_session)
    assert success is True

    # Step 5: Verify Change & Analysis status is now COMPLETED
    status_resp_2 = client.get(f"/api/v1/changes/{change_id}/status", headers=headers)
    assert status_resp_2.status_code == 200
    assert status_resp_2.json()["data"]["status"] == "COMPLETED"

    # Step 6: Verify full Change Detail response consumed by frontend
    detail_resp = client.get(f"/api/v1/changes/{change_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]

    assert detail["id"] == change_id
    assert detail["status"] == "COMPLETED"
    assert detail["commit_sha"] == commit_sha
    assert detail["pull_request"]["number"] == pr_number
    assert detail["pull_request"]["title"] == "Add organization profile endpoint"
    assert detail["pull_request"]["author"] == "octocat"
    assert detail["repository"]["full_name"] == "proofmesh-demo-org/demo-enterprise"

    # Verify Analysis Run details
    assert len(detail["analysis_runs"]) == 1
    run_detail = detail["analysis_runs"][0]
    assert run_detail["id"] == analysis_run_id
    assert run_detail["status"] == "COMPLETED"
    assert run_detail["stage"] in {"INGESTION_VALIDATION", "DEPENDENCY_ANALYSIS", "POLICY_EVALUATION"}
    assert run_detail["worker_id"] == "worker-e2e-test"
    assert run_detail["started_at"] is not None
    assert run_detail["completed_at"] is not None

    # Verify Audit trail
    audit_actions = [log["action"] for log in detail["audit_history"]]
    assert "PR_INGESTED" in audit_actions
    assert "CHANGE_CREATED" in audit_actions
    assert "ANALYSIS_QUEUED" in audit_actions
    assert "ANALYSIS_STARTED" in audit_actions
    assert "ANALYSIS_COMPLETED" in audit_actions
