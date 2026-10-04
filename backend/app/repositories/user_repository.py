from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.models.entities import User, UserOrganizationMembership


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.memberships).joinedload(UserOrganizationMembership.organization))
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.memberships).joinedload(UserOrganizationMembership.organization))
            .filter(User.email == email.lower().strip())
            .first()
        )

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
