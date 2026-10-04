from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
