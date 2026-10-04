from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.entities import Organization, UserOrganizationMembership


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: str) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.id == org_id).first()

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.slug == slug.lower().strip()).first()

    def create(self, org: Organization) -> Organization:
        self.db.add(org)
        self.db.flush()
        return org

    def add_member(self, membership: UserOrganizationMembership) -> UserOrganizationMembership:
        self.db.add(membership)
        self.db.flush()
        return membership

    def get_user_organizations(self, user_id: str) -> List[Organization]:
        return (
            self.db.query(Organization)
            .join(UserOrganizationMembership, UserOrganizationMembership.organization_id == Organization.id)
            .filter(UserOrganizationMembership.user_id == user_id)
            .all()
        )
