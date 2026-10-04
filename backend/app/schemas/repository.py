from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RepositoryCreate(BaseModel):
    github_repository_id: str = Field(..., description="GitHub unique repository ID")
    owner: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    default_branch: str = Field("main")
    organization_id: Optional[str] = None


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: str
    github_repository_id: str
    owner: str
    name: str
    full_name: str
    default_branch: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
