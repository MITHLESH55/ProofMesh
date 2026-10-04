from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.repository import RepositoryResponse
from app.schemas.pull_request import PullRequestResponse
from app.schemas.analysis import AnalysisRunResponse
from app.schemas.audit import AuditLogResponse


class ChangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    pull_request_id: str
    commit_sha: str
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    pull_request: Optional[PullRequestResponse] = None
    repository: Optional[RepositoryResponse] = None
    latest_analysis_run: Optional[AnalysisRunResponse] = None


class ChangeDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    pull_request_id: str
    commit_sha: str
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    pull_request: PullRequestResponse
    repository: RepositoryResponse
    analysis_runs: List[AnalysisRunResponse]
    audit_history: List[AuditLogResponse]


class ChangeStatusResponse(BaseModel):
    change_id: str
    status: str
    latest_analysis_run: Optional[AnalysisRunResponse] = None
    updated_at: datetime


class ReanalyzeRequest(BaseModel):
    reason: Optional[str] = "Manual reanalysis request"
