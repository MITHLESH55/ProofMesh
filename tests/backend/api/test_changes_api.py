import pytest
from fastapi.testclient import TestClient
from app.models.entities import Change, ChangeStatus, Organization, PullRequest, Repository


def test_changes_api_endpoints(client: TestClient, db_session, test_engineer_token: str):
    # Setup test entities
    org = Organization(name="Change Test Org", slug="change-test-org")
    db_session.add(org)
    db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repository_id="777666",
        owner="change-test-org",
        name="service-api",
        full_name="change-test-org/service-api",
    )
    db_session.add(repo)
    db_session.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="111222",
        number=10,
        title="Implement change tracking",
        author="engineer",
        head_sha="1234567890abcdef1234567890abcdef12345678",
        base_sha="0000000000000000000000000000000000000000",
    )
    db_session.add(pr)
    db_session.flush()

    change = Change(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status=ChangeStatus.COMPLETED.value,
    )
    db_session.add(change)
    db_session.commit()

    headers = {"Authorization": f"Bearer {test_engineer_token}"}

    # 1. List changes
    list_resp = client.get("/api/v1/changes", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data["data"]) >= 1

    # 2. Get change by ID
    get_resp = client.get(f"/api/v1/changes/{change.id}", headers=headers)
    assert get_resp.status_code == 200
    detail_data = get_resp.json()["data"]
    assert detail_data["id"] == change.id
    assert detail_data["pull_request"]["title"] == "Implement change tracking"
    assert detail_data["repository"]["name"] == "service-api"

    # 3. Get change status
    status_resp = client.get(f"/api/v1/changes/{change.id}/status", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["status"] == "COMPLETED"

    # 4. Retrigger analysis
    reanalyze_resp = client.post(
        f"/api/v1/changes/{change.id}/reanalyze",
        json={"reason": "Test manual reanalyze"},
        headers=headers,
    )
    assert reanalyze_resp.status_code == 200
    reanalyze_data = reanalyze_resp.json()["data"]
    assert reanalyze_data["status"] == "QUEUED"
    assert len(reanalyze_data["analysis_runs"]) >= 1
