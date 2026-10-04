from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.entities import Repository


class RepositoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, repo_id: str) -> Optional[Repository]:
        return self.db.query(Repository).filter(Repository.id == repo_id).first()

    def get_by_github_id(self, github_repo_id: str) -> Optional[Repository]:
        return self.db.query(Repository).filter(Repository.github_repository_id == str(github_repo_id)).first()

    def get_by_full_name(self, full_name: str) -> Optional[Repository]:
        return self.db.query(Repository).filter(Repository.full_name == full_name).first()

    def list_by_organization(self, organization_id: Optional[str] = None) -> List[Repository]:
        query = self.db.query(Repository)
        if organization_id:
            query = query.filter(Repository.organization_id == organization_id)
        return query.order_by(Repository.updated_at.desc()).all()

    def create(self, repo: Repository) -> Repository:
        self.db.add(repo)
        self.db.flush()
        return repo

    def update(self, repo: Repository) -> Repository:
        self.db.flush()
        return repo
