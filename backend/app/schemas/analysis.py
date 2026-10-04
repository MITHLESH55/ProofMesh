from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AnalysisRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    change_id: str
    status: str
    stage: str
    worker_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


class AnalysisRunCreate(BaseModel):
    change_id: str
    stage: str = "INGESTION_VALIDATION"
