from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.entities import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_by_entity(self, entity_type: str, entity_id: str) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.created_at.asc())
            .all()
        )

    def list_by_organization(self, organization_id: str, limit: int = 100) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
