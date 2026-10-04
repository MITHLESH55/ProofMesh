from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.errors import BadRequestError, ConflictError
from app.core.logging import logger
from app.models.entities import (
    AnalysisRun,
    AnalysisStatus,
    Change,
    ChangeStatus,
    Organization,
    PullRequest,
    PullRequestState,
    Repository,
    UserRole,
)
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.change_repository import ChangeRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.pull_request_repository import PullRequestRepository
from app.repositories.repository_repository import RepositoryRepository
from app.repositories.webhook_event_repository import WebhookEventRepository
from app.schemas.webhook import GitHubWebhookPayload
from app.services.audit.service import AuditService
from app.services.jobs.queue import job_queue


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo_repo = RepositoryRepository(db)
        self.pr_repo = PullRequestRepository(db)
        self.change_repo = ChangeRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.webhook_event_repo = WebhookEventRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.audit_service = AuditService(db)

    def _get_or_create_default_org(self) -> Organization:
        default_slug = "default"
        org = self.org_repo.get_by_slug(default_slug)
        if not org:
            org = Organization(name="Default Organization", slug=default_slug)
            self.org_repo.create(org)
            self.db.flush()
        return org

    def handle_github_webhook(
        self,
        event_type: str,
        payload: GitHubWebhookPayload,
        delivery_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Idempotently processes GitHub webhook events in a transactional scope.
        """
        # 1. Webhook Idempotency check via Delivery ID
        if delivery_id:
            existing_event = self.webhook_event_repo.get_by_delivery_id(delivery_id)
            if existing_event:
                logger.info(
                    f"Duplicate webhook delivery {delivery_id} for event {event_type} ignored.",
                    extra={"delivery_id": delivery_id, "event_type": event_type, "request_id": request_id}
                )
                return {
                    "status": "duplicate_ignored",
                    "delivery_id": delivery_id,
                    "event_type": event_type,
                    "message": "Webhook delivery was previously processed",
                }

        # 2. Check if event is pull_request
        if event_type != "pull_request":
            logger.info(
                f"Ignoring unsupported GitHub event type: {event_type}",
                extra={"event_type": event_type, "request_id": request_id}
            )
            if delivery_id:
                self.webhook_event_repo.record_processed(delivery_id, event_type)
                self.db.commit()
            return {
                "status": "unsupported_event_ignored",
                "event_type": event_type,
                "message": f"Event type '{event_type}' is not handled in Phase 1",
            }

        action = payload.action
        if action not in {"opened", "synchronize", "reopened", "closed"}:
            logger.info(
                f"Ignoring unhandled pull_request action: {action}",
                extra={"event_type": event_type, "action": action, "request_id": request_id}
            )
            if delivery_id:
                self.webhook_event_repo.record_processed(delivery_id, f"{event_type}.{action}")
                self.db.commit()
            return {
                "status": "action_ignored",
                "action": action,
                "message": f"PR action '{action}' is not handled in Phase 1",
            }

        if not payload.repository or not payload.pull_request:
            raise BadRequestError("Webhook payload missing repository or pull_request details", code="INVALID_PAYLOAD")

        try:
            # 3. Find or Create Repository
            repo_payload = payload.repository
            github_repo_id = str(repo_payload.id)
            repo = self.repo_repo.get_by_github_id(github_repo_id)
            if not repo:
                default_org = self._get_or_create_default_org()
                repo = Repository(
                    organization_id=default_org.id,
                    github_repository_id=github_repo_id,
                    owner=repo_payload.owner.login,
                    name=repo_payload.name,
                    full_name=repo_payload.full_name,
                    default_branch=repo_payload.default_branch,
                    is_active=True,
                )
                self.repo_repo.create(repo)
                self.audit_service.log(
                    action="REPOSITORY_CONNECTED",
                    entity_type="REPOSITORY",
                    entity_id=repo.id,
                    organization_id=repo.organization_id,
                    metadata={"full_name": repo.full_name, "github_id": github_repo_id},
                )
            else:
                repo.owner = repo_payload.owner.login
                repo.name = repo_payload.name
                repo.full_name = repo_payload.full_name
                repo.default_branch = repo_payload.default_branch
                self.repo_repo.update(repo)

            # 4. Find or Create Pull Request
            pr_payload = payload.pull_request
            pr = self.pr_repo.get_by_repo_and_number(repo.id, pr_payload.number)
            pr_state = (
                PullRequestState.MERGED.value
                if pr_payload.merged_at
                else (PullRequestState.CLOSED.value if pr_payload.state == "closed" else PullRequestState.OPEN.value)
            )

            if not pr:
                pr = PullRequest(
                    repository_id=repo.id,
                    github_pr_id=str(pr_payload.id),
                    number=pr_payload.number,
                    title=pr_payload.title,
                    description=pr_payload.body,
                    author=pr_payload.user.login,
                    head_sha=pr_payload.head.sha,
                    base_sha=pr_payload.base.sha,
                    state=pr_state,
                    opened_at=pr_payload.created_at or datetime.now(timezone.utc),
                    updated_at=pr_payload.updated_at,
                    closed_at=pr_payload.closed_at,
                )
                self.pr_repo.create(pr)
                self.audit_service.log(
                    action="PR_INGESTED",
                    entity_type="PULL_REQUEST",
                    entity_id=pr.id,
                    organization_id=repo.organization_id,
                    metadata={"number": pr.number, "title": pr.title, "head_sha": pr.head_sha},
                )
            else:
                pr.title = pr_payload.title
                pr.description = pr_payload.body
                pr.head_sha = pr_payload.head.sha
                pr.base_sha = pr_payload.base.sha
                pr.state = pr_state
                pr.updated_at = pr_payload.updated_at or datetime.now(timezone.utc)
                if pr_payload.closed_at:
                    pr.closed_at = pr_payload.closed_at
                self.pr_repo.update(pr)

            # 5. Handle action-specific Change & Analysis lifecycle
            result_data = {
                "repository_id": repo.id,
                "pull_request_id": pr.id,
                "pr_number": pr.number,
                "action": action,
            }

            if action in {"opened", "synchronize", "reopened"}:
                commit_sha = pr_payload.head.sha

                # Find or create Change
                change = self.change_repo.get_by_pr_and_commit(pr.id, commit_sha)
                if not change:
                    change = Change(
                        pull_request_id=pr.id,
                        commit_sha=commit_sha,
                        status=ChangeStatus.QUEUED.value,
                        source="GITHUB_WEBHOOK",
                    )
                    self.change_repo.create(change)
                    self.audit_service.log(
                        action="CHANGE_CREATED",
                        entity_type="CHANGE",
                        entity_id=change.id,
                        organization_id=repo.organization_id,
                        metadata={"commit_sha": commit_sha, "pr_number": pr.number},
                    )
                else:
                    change.status = ChangeStatus.QUEUED.value
                    self.change_repo.update(change)

                # Create new Analysis Run
                analysis_run = AnalysisRun(
                    change_id=change.id,
                    status=AnalysisStatus.QUEUED.value,
                    stage="INGESTION_VALIDATION",
                )
                self.analysis_repo.create(analysis_run)

                self.audit_service.log(
                    action="ANALYSIS_QUEUED",
                    entity_type="ANALYSIS_RUN",
                    entity_id=analysis_run.id,
                    organization_id=repo.organization_id,
                    metadata={"change_id": change.id, "stage": "INGESTION_VALIDATION"},
                )

                # Record delivery ID if provided
                if delivery_id:
                    self.webhook_event_repo.record_processed(delivery_id, f"{event_type}.{action}")

                # Commit DB transaction before enqueuing to worker
                self.db.commit()

                # Enqueue job to worker queue
                job_queue.enqueue_analysis(change_id=change.id, analysis_run_id=analysis_run.id)

                result_data.update({
                    "change_id": change.id,
                    "analysis_run_id": analysis_run.id,
                    "status": "queued",
                    "commit_sha": commit_sha,
                })

            elif action == "closed":
                self.audit_service.log(
                    action="PR_CLOSED",
                    entity_type="PULL_REQUEST",
                    entity_id=pr.id,
                    organization_id=repo.organization_id,
                    metadata={"number": pr.number, "state": pr_state},
                )
                if delivery_id:
                    self.webhook_event_repo.record_processed(delivery_id, f"{event_type}.{action}")
                self.db.commit()
                result_data.update({"status": "pr_closed", "state": pr_state})

            return result_data

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed processing GitHub webhook: {str(e)}",
                extra={"delivery_id": delivery_id, "event_type": event_type, "request_id": request_id},
                exc_info=True
            )
            raise e
