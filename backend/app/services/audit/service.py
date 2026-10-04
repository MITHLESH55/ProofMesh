from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.entities import AuditLog
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditRepository(db)

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        organization_id: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_metadata=metadata or {},
        )
        return self.repo.create(audit_log)
