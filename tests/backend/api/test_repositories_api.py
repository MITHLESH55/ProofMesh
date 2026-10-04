import pytest
from fastapi.testclient import TestClient


def test_repositories_create_and_list(client: TestClient, test_admin_token: str, test_engineer_token: str):
    # Create repository as ADMIN
    create_payload = {
        "github_repository_id": "123456789",
        "owner": "test-org",
        "name": "core-engine",
        "default_branch": "main",
    }
    resp = client.post(
        "/api/v1/repositories",
        json=create_payload,
        headers={"Authorization": f"Bearer {test_admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    repo_id = data["data"]["id"]
    assert data["data"]["name"] == "core-engine"
    assert data["data"]["full_name"] == "test-org/core-engine"

    # List repositories
    list_resp = client.get(
        "/api/v1/repositories",
        headers={"Authorization": f"Bearer {test_engineer_token}"},
    )
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data["data"]) >= 1

    # Get repository by ID
    get_resp = client.get(
        f"/api/v1/repositories/{repo_id}",
        headers={"Authorization": f"Bearer {test_engineer_token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["id"] == repo_id


def test_repositories_create_forbidden_for_engineer(client: TestClient, test_engineer_token: str):
    # Attempt repo creation as ENGINEER (should be 403 Forbidden)
    create_payload = {
        "github_repository_id": "999888777",
        "owner": "test-org",
        "name": "unauthorized-repo",
    }
    resp = client.post(
        "/api/v1/repositories",
        json=create_payload,
        headers={"Authorization": f"Bearer {test_engineer_token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"
