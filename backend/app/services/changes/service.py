from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.errors import NotFoundError
from app.models.entities import AnalysisRun, AnalysisStatus, Change, ChangeStatus, User
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.change_repository import ChangeRepository
from app.schemas.analysis import AnalysisRunResponse
from app.schemas.audit import AuditLogResponse
from app.schemas.change import ChangeDetailResponse, ChangeResponse, ChangeStatusResponse
from app.schemas.pull_request import PullRequestResponse
from app.schemas.repository import RepositoryResponse
from app.services.audit.service import AuditService
from app.services.jobs.queue import job_queue


class ChangesService:
    def __init__(self, db: Session):
        self.db = db
        self.change_repo = ChangeRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.audit_repo = AuditRepository(db)
        self.audit_service = AuditService(db)

    def list_changes(
        self,
        repository_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ChangeResponse], int]:
        changes, total = self.change_repo.list_changes(
            repository_id=repository_id,
            status=status,
            limit=limit,
            offset=offset,
        )

        responses = []
        for c in changes:
            latest_run = self.analysis_repo.get_latest_for_change(c.id)
            responses.append(
                ChangeResponse(
                    id=c.id,
                    pull_request_id=c.pull_request_id,
                    commit_sha=c.commit_sha,
                    status=c.status,
                    source=c.source,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    pull_request=PullRequestResponse.model_validate(c.pull_request) if c.pull_request else None,
                    repository=RepositoryResponse.model_validate(c.pull_request.repository) if c.pull_request and c.pull_request.repository else None,
                    latest_analysis_run=AnalysisRunResponse.model_validate(latest_run) if latest_run else None,
                )
            )
        return responses, total

    def get_change_by_id(self, change_id: str) -> ChangeDetailResponse:
        change = self.change_repo.get_by_id(change_id)
        if not change:
            raise NotFoundError(f"Change with ID '{change_id}' not found", code="CHANGE_NOT_FOUND")

        runs = self.analysis_repo.list_by_change(change.id)
        audit_logs = self.audit_repo.list_by_entity(entity_type="CHANGE", entity_id=change.id)

        # Also grab audit logs for PR and analysis runs
        pr_logs = self.audit_repo.list_by_entity(entity_type="PULL_REQUEST", entity_id=change.pull_request_id)
        run_logs = []
        for r in runs:
            run_logs.extend(self.audit_repo.list_by_entity(entity_type="ANALYSIS_RUN", entity_id=r.id))

        all_logs = sorted(audit_logs + pr_logs + run_logs, key=lambda x: x.created_at)

        return ChangeDetailResponse(
            id=change.id,
            pull_request_id=change.pull_request_id,
            commit_sha=change.commit_sha,
            status=change.status,
            source=change.source,
            created_at=change.created_at,
            updated_at=change.updated_at,
            pull_request=PullRequestResponse.model_validate(change.pull_request),
            repository=RepositoryResponse.model_validate(change.pull_request.repository),
            analysis_runs=[AnalysisRunResponse.model_validate(r) for r in runs],
            audit_history=[AuditLogResponse.model_validate(l) for l in all_logs],
        )

    def get_change_status(self, change_id: str) -> ChangeStatusResponse:
        change = self.change_repo.get_by_id(change_id)
        if not change:
            raise NotFoundError(f"Change with ID '{change_id}' not found", code="CHANGE_NOT_FOUND")

        latest_run = self.analysis_repo.get_latest_for_change(change.id)
        return ChangeStatusResponse(
            change_id=change.id,
            status=change.status,
            latest_analysis_run=AnalysisRunResponse.model_validate(latest_run) if latest_run else None,
            updated_at=change.updated_at,
        )

    def reanalyze(self, change_id: str, actor_user: Optional[User] = None, reason: Optional[str] = None) -> ChangeDetailResponse:
        change = self.change_repo.get_by_id(change_id)
        if not change:
            raise NotFoundError(f"Change with ID '{change_id}' not found", code="CHANGE_NOT_FOUND")

        # Update change status to QUEUED
        change.status = ChangeStatus.QUEUED.value
        self.change_repo.update(change)

        # Create new analysis run
        analysis_run = AnalysisRun(
            change_id=change.id,
            status=AnalysisStatus.QUEUED.value,
            stage="INGESTION_VALIDATION",
        )
        self.analysis_repo.create(analysis_run)

        # Audit log
        org_id = change.pull_request.repository.organization_id if change.pull_request and change.pull_request.repository else None
        self.audit_service.log(
            action="ANALYSIS_RETRIGGERED",
            entity_type="CHANGE",
            entity_id=change.id,
            organization_id=org_id,
            actor_user_id=actor_user.id if actor_user else None,
            metadata={"reason": reason or "Manual retrigger", "analysis_run_id": analysis_run.id},
        )
        self.db.commit()

        # Enqueue job
        job_queue.enqueue_analysis(change_id=change.id, analysis_run_id=analysis_run.id)

        return self.get_change_by_id(change.id)
