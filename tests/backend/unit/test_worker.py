import pytest
from app.models.entities import (
    AnalysisRun,
    AnalysisStatus,
    Change,
    ChangeStatus,
    Organization,
    PullRequest,
    Repository,
)
from app.workers.worker import AnalysisWorker


def test_worker_job_processing_success(db_session):
    # Setup test DB entities
    org = Organization(name="Test Org", slug="test-org")
    db_session.add(org)
    db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repository_id="111222",
        owner="test-org",
        name="test-repo",
        full_name="test-org/test-repo",
    )
    db_session.add(repo)
    db_session.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="333444",
        number=1,
        title="Test PR",
        author="developer",
        head_sha="abcdef1234567890abcdef1234567890abcdef12",
        base_sha="0000000000000000000000000000000000000000",
    )
    db_session.add(pr)
    db_session.flush()

    change = Change(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status=ChangeStatus.QUEUED.value,
    )
    db_session.add(change)
    db_session.flush()

    run = AnalysisRun(
        change_id=change.id,
        status=AnalysisStatus.QUEUED.value,
        stage="INGESTION_VALIDATION",
    )
    db_session.add(run)
    db_session.commit()

    # Process job via worker
    worker = AnalysisWorker(worker_id="test-worker-01")
    job_payload = {
        "change_id": change.id,
        "analysis_run_id": run.id,
        "attempt": 1,
        "max_attempts": 3,
    }

    success = worker.process_job(job_payload, db_session)
    assert success is True

    # Refresh entities
    db_session.refresh(change)
    db_session.refresh(run)

    assert change.status == ChangeStatus.COMPLETED.value
    assert run.status == AnalysisStatus.COMPLETED.value
    assert run.worker_id == "test-worker-01"
    assert run.started_at is not None
    assert run.completed_at is not None
    assert run.error_message is None


def test_worker_job_processing_failure_invalid_commit(db_session):
    org = Organization(name="Test Org 2", slug="test-org-2")
    db_session.add(org)
    db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repository_id="555666",
        owner="test-org",
        name="test-repo-2",
        full_name="test-org/test-repo-2",
    )
    db_session.add(repo)
    db_session.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="777888",
        number=2,
        title="Test PR Invalid",
        author="developer",
        head_sha="short",  # Invalid short commit SHA (<7 chars)
        base_sha="000000",
    )
    db_session.add(pr)
    db_session.flush()

    change = Change(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status=ChangeStatus.QUEUED.value,
    )
    db_session.add(change)
    db_session.flush()

    run = AnalysisRun(
        change_id=change.id,
        status=AnalysisStatus.QUEUED.value,
        stage="INGESTION_VALIDATION",
    )
    db_session.add(run)
    db_session.commit()

    worker = AnalysisWorker(worker_id="test-worker-02")
    job_payload = {
        "change_id": change.id,
        "analysis_run_id": run.id,
        "attempt": 3,  # Max attempts reached
        "max_attempts": 3,
    }

    success = worker.process_job(job_payload, db_session)
    assert success is False

    db_session.refresh(change)
    db_session.refresh(run)

    assert change.status == ChangeStatus.FAILED.value
    assert run.status == AnalysisStatus.FAILED.value
    assert "Invalid commit SHA" in run.error_message
