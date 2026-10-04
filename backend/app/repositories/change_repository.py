from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.entities import Change, PullRequest, Repository, AnalysisRun


class ChangeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, change_id: str) -> Optional[Change]:
        return (
            self.db.query(Change)
            .options(
                joinedload(Change.pull_request).joinedload(PullRequest.repository),
                selectinload(Change.analysis_runs),
            )
            .filter(Change.id == change_id)
            .first()
        )

    def get_by_pr_and_commit(self, pull_request_id: str, commit_sha: str) -> Optional[Change]:
        return (
            self.db.query(Change)
            .options(
                joinedload(Change.pull_request).joinedload(PullRequest.repository),
                selectinload(Change.analysis_runs),
            )
            .filter(
                Change.pull_request_id == pull_request_id,
                Change.commit_sha == commit_sha
            )
            .first()
        )

    def list_changes(
        self,
        repository_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Change], int]:
        query = (
            self.db.query(Change)
            .options(
                joinedload(Change.pull_request).joinedload(PullRequest.repository),
                selectinload(Change.analysis_runs),
            )
            .join(Change.pull_request)
        )

        if repository_id:
            query = query.filter(PullRequest.repository_id == repository_id)

        if status:
            query = query.filter(Change.status == status.upper())

        total = query.count()
        results = query.order_by(Change.created_at.desc()).offset(offset).limit(limit).all()
        return results, total

    def create(self, change: Change) -> Change:
        self.db.add(change)
        self.db.flush()
        return change

    def update(self, change: Change) -> Change:
        self.db.flush()
        return change
