import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings


def generate_signature(body: bytes, secret: str = settings.GITHUB_WEBHOOK_SECRET) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def build_pr_payload(
    action: str = "opened",
    pr_number: int = 1,
    repo_id: int = 999999,
    head_sha: str = "abcdef1234567890abcdef1234567890abcdef12",
):
    return {
        "action": action,
        "number": pr_number,
        "repository": {
            "id": repo_id,
            "name": "enterprise-backend",
            "full_name": "acme/enterprise-backend",
            "owner": {"login": "acme", "id": 10},
            "default_branch": "main",
        },
        "pull_request": {
            "id": 88888 + pr_number,
            "number": pr_number,
            "title": f"Feature change #{pr_number}",
            "body": "PR description body",
            "user": {"login": "alice", "id": 101},
            "head": {"sha": head_sha},
            "base": {"sha": "0000000000000000000000000000000000000000"},
            "state": "open",
        },
    }


def test_webhook_test_a_valid_signature_accepted(client: TestClient):
    payload = build_pr_payload(action="opened", pr_number=101)
    body = json.dumps(payload).encode("utf-8")
    sig = generate_signature(body)

    resp = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-valid-001",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["action"] == "opened"
    assert data["data"]["status"] == "queued"
    assert data["data"]["pr_number"] == 101


def test_webhook_test_b_invalid_signature_rejected(client: TestClient):
    payload = build_pr_payload(action="opened", pr_number=102)
    body = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": "sha256=invalid_hex_signature_here",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-invalid-002",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_WEBHOOK_SIGNATURE"


def test_webhook_test_c_duplicate_delivery_idempotent(client: TestClient):
    payload = build_pr_payload(action="opened", pr_number=103)
    body = json.dumps(payload).encode("utf-8")
    sig = generate_signature(body)
    delivery_id = "delivery-duplicate-test-003"

    # First delivery
    resp1 = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": delivery_id,
            "Content-Type": "application/json",
        },
    )
    assert resp1.status_code == 200
    assert resp1.json()["data"]["status"] == "queued"

    # Repeated identical delivery (idempotency check)
    resp2 = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": delivery_id,
            "Content-Type": "application/json",
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["data"]["status"] == "duplicate_ignored"


def test_webhook_test_d_pr_synchronize_creates_new_commit_run(client: TestClient):
    repo_id = 777123
    pr_number = 104

    # 1. PR Opened with initial commit
    sha1 = "1111111111111111111111111111111111111111"
    payload1 = build_pr_payload(action="opened", pr_number=pr_number, repo_id=repo_id, head_sha=sha1)
    body1 = json.dumps(payload1).encode("utf-8")
    resp1 = client.post(
        "/api/v1/webhooks/github",
        content=body1,
        headers={
            "X-Hub-Signature-256": generate_signature(body1),
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-sync-01",
            "Content-Type": "application/json",
        },
    )
    assert resp1.status_code == 200
    change_id_1 = resp1.json()["data"]["change_id"]

    # 2. PR Synchronize with new commit SHA
    sha2 = "2222222222222222222222222222222222222222"
    payload2 = build_pr_payload(action="synchronize", pr_number=pr_number, repo_id=repo_id, head_sha=sha2)
    body2 = json.dumps(payload2).encode("utf-8")
    resp2 = client.post(
        "/api/v1/webhooks/github",
        content=body2,
        headers={
            "X-Hub-Signature-256": generate_signature(body2),
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-sync-02",
            "Content-Type": "application/json",
        },
    )
    assert resp2.status_code == 200
    change_id_2 = resp2.json()["data"]["change_id"]
    assert change_id_2 != change_id_1
    assert resp2.json()["data"]["commit_sha"] == sha2


def test_webhook_test_e_unsupported_event_handled_safely(client: TestClient):
    body = json.dumps({"zen": "Keep it logically awesome."}).encode("utf-8")
    sig = generate_signature(body)

    resp = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "delivery-ping-01",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "unsupported_event_ignored"
