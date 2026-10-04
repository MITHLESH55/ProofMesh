from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.entities import PullRequest


class PullRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, pr_id: str) -> Optional[PullRequest]:
        return self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()

    def get_by_repo_and_number(self, repository_id: str, number: int) -> Optional[PullRequest]:
        return (
            self.db.query(PullRequest)
            .filter(PullRequest.repository_id == repository_id, PullRequest.number == number)
            .first()
        )

    def create(self, pr: PullRequest) -> PullRequest:
        self.db.add(pr)
        self.db.flush()
        return pr

    def update(self, pr: PullRequest) -> PullRequest:
        self.db.flush()
        return pr
