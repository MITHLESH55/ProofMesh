"""
Pydantic schemas for Phase 5 Enterprise Intelligence — Teams, Services, Ownership, Cross-Repo Dependencies, Historical Evidence, Incidents.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Team Schemas ---

class TeamCreate(BaseModel):
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None


class TeamResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime


# --- Service Schemas ---

class ServiceCreate(BaseModel):
    organization_id: str
    team_id: Optional[str] = None
    repository_id: Optional[str] = None
    name: str
    criticality: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    description: Optional[str] = None
    tier: int = 2


class ServiceResponse(BaseModel):
    id: str
    organization_id: str
    team_id: Optional[str] = None
    repository_id: Optional[str] = None
    name: str
    criticality: str
    description: Optional[str] = None
    tier: int
    created_at: datetime


# --- Component Ownership Schemas ---

class ComponentOwnershipCreate(BaseModel):
    service_id: Optional[str] = None
    repository_id: str
    component_path: str
    owner_team_id: Optional[str] = None
    owner_user_id: Optional[str] = None
    source: str = "EXPLICIT"


class ComponentOwnershipResponse(BaseModel):
    id: str
    service_id: Optional[str] = None
    repository_id: str
    component_path: str
    owner_team_id: Optional[str] = None
    owner_user_id: Optional[str] = None
    source: str
    created_at: datetime


# --- Cross-Repository Dependency Schemas ---

class CrossRepoDependencyCreate(BaseModel):
    organization_id: str
    source_repository_id: str
    target_repository_id: str
    dependency_type: str  # PACKAGE, API_CALL, EVENT_STREAM, SHARED_LIB
    package_or_service_name: str
    provenance_details: Dict[str, Any] = Field(default_factory=dict)


class CrossRepoDependencyResponse(BaseModel):
    id: str
    organization_id: str
    source_repository_id: str
    target_repository_id: str
    dependency_type: str
    package_or_service_name: str
    provenance_details: Dict[str, Any]
    created_at: datetime


# --- Enterprise Graph & Versions ---

class EnterpriseGraphVersionResponse(BaseModel):
    id: str
    organization_id: str
    version_tag: str
    commit_sha: str
    graph_snapshot_ref: Optional[str] = None
    node_count: int
    edge_count: int
    analyzed_at: datetime


class EnterpriseGraphNode(BaseModel):
    id: str
    label: str
    type: str  # REPOSITORY, SERVICE, TEAM, API, DATABASE
    criticality: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnterpriseGraphEdge(BaseModel):
    source: str
    target: str
    type: str  # DEPENDS_ON, OWNS, CALLS_API, IMPORTS_PACKAGE, PRODUCES_EVENT
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnterpriseGraphResponse(BaseModel):
    organization_id: str
    nodes: List[EnterpriseGraphNode]
    edges: List[EnterpriseGraphEdge]
    total_services: int
    total_repositories: int


# --- Historical Evidence & Search Schemas ---

class HistoricalEvidenceCreate(BaseModel):
    organization_id: str
    repository_id: Optional[str] = None
    evidence_type: str  # PROOF_SUMMARY, INCIDENT, REGRESSION, REMEDIATION, TEST_RATIONALE
    title: str
    content: str
    embedding: Optional[List[float]] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class HistoricalEvidenceResponse(BaseModel):
    id: str
    organization_id: str
    repository_id: Optional[str] = None
    evidence_type: str
    title: str
    content: str
    provenance: Dict[str, Any]
    created_at: datetime


class EvidenceSearchRequest(BaseModel):
    query: str
    organization_id: Optional[str] = None
    repository_id: Optional[str] = None
    evidence_type: Optional[str] = None
    limit: int = 5


class EvidenceSearchResult(BaseModel):
    id: str
    evidence_type: str
    title: str
    content: str
    similarity_score: float
    provenance: Dict[str, Any]
    created_at: datetime


# --- Incident Record Schemas ---

class IncidentRecordCreate(BaseModel):
    organization_id: str
    service_id: Optional[str] = None
    change_id: Optional[str] = None
    severity: str = "HIGH"
    summary: str
    root_cause: str
    regression_metric: Optional[str] = None
    resolved_at: Optional[datetime] = None


class IncidentRecordResponse(BaseModel):
    id: str
    organization_id: str
    service_id: Optional[str] = None
    change_id: Optional[str] = None
    severity: str
    summary: str
    root_cause: str
    regression_metric: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


# --- Enterprise Overview ---

class EnterpriseOverviewResponse(BaseModel):
    total_organizations: int
    total_teams: int
    total_repositories: int
    total_services: int
    critical_services_count: int
    total_cross_repo_deps: int
    active_incidents_count: int
    active_agents_count: int
