from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class GitHubUserPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    login: str
    id: Optional[int] = None


class GitHubRepoPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    name: str
    full_name: str
    owner: GitHubUserPayload
    default_branch: str = "main"


class GitHubPRCommitPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    sha: str


class GitHubPRPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    number: int
    title: str
    body: Optional[str] = None
    user: GitHubUserPayload
    head: GitHubPRCommitPayload
    base: GitHubPRCommitPayload
    state: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None


class GitHubWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    action: Optional[str] = None
    number: Optional[int] = None
    pull_request: Optional[GitHubPRPayload] = None
    repository: Optional[GitHubRepoPayload] = None
    sender: Optional[GitHubUserPayload] = None
