from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PullRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    repository_id: str
    github_pr_id: str
    number: int
    title: str
    description: Optional[str] = None
    author: str
    head_sha: str
    base_sha: str
    state: str
    opened_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
