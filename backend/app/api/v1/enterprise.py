"""
Phase 5 Enterprise API Endpoints.

Provides endpoints for:
- Team CRUD and listing
- Service CRUD with criticality management
- Component ownership assignment
- Cross-repository dependency tracking
- Enterprise Software Graph construction and visualization
- Historical evidence storage and semantic search
- Incident record management
- Enterprise health overview dashboard
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.core.logging import logger
from app.db.session import get_db
from app.models.entities import User
from app.schemas.common import SuccessEnvelope
from app.schemas.enterprise import (
    TeamCreate,
    TeamResponse,
    ServiceCreate,
    ServiceResponse,
    ComponentOwnershipCreate,
    ComponentOwnershipResponse,
    CrossRepoDependencyCreate,
    CrossRepoDependencyResponse,
    EnterpriseGraphResponse,
    EnterpriseGraphVersionResponse,
    HistoricalEvidenceCreate,
    HistoricalEvidenceResponse,
    EvidenceSearchRequest,
    EvidenceSearchResult,
    IncidentRecordCreate,
    IncidentRecordResponse,
    EnterpriseOverviewResponse,
)
from app.services.enterprise import (
    EnterpriseService,
    EnterpriseGraphService,
    HistoricalEvidenceService,
)
from app.models.enterprise import IncidentRecord
from app.services.auth.service import get_current_user

router = APIRouter(prefix="/enterprise", tags=["Enterprise Intelligence"])


# ─── Teams ───

@router.post("/teams", response_model=SuccessEnvelope[TeamResponse], summary="Create Team")
def create_team(
    data: TeamCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new engineering team in the enterprise."""
    team = EnterpriseService.create_team(db, data)
    return SuccessEnvelope(
        data=TeamResponse(
            id=team.id,
            organization_id=team.organization_id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            created_at=team.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_team"),
    )


@router.get("/teams", response_model=SuccessEnvelope[List[TeamResponse]], summary="List Teams")
def list_teams(
    request: Request,
    organization_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List engineering teams, optionally filtered by organization."""
    teams = EnterpriseService.list_teams(db, organization_id=organization_id)
    return SuccessEnvelope(
        data=[
            TeamResponse(
                id=t.id,
                organization_id=t.organization_id,
                name=t.name,
                slug=t.slug,
                description=t.description,
                created_at=t.created_at,
            )
            for t in teams
        ],
        request_id=getattr(request.state, "request_id", "req_teams"),
    )


# ─── Services ───

@router.post("/services", response_model=SuccessEnvelope[ServiceResponse], summary="Create Service")
def create_service(
    data: ServiceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a microservice or component with criticality and ownership."""
    service = EnterpriseService.create_service(db, data)
    return SuccessEnvelope(
        data=ServiceResponse(
            id=service.id,
            organization_id=service.organization_id,
            team_id=service.team_id,
            repository_id=service.repository_id,
            name=service.name,
            criticality=service.criticality,
            description=service.description,
            tier=service.tier,
            created_at=service.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_service"),
    )


@router.get("/services", response_model=SuccessEnvelope[List[ServiceResponse]], summary="List Services")
def list_services(
    request: Request,
    organization_id: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List services, optionally filtered by organization and criticality."""
    services = EnterpriseService.list_services(db, organization_id=organization_id, criticality=criticality)
    return SuccessEnvelope(
        data=[
            ServiceResponse(
                id=s.id,
                organization_id=s.organization_id,
                team_id=s.team_id,
                repository_id=s.repository_id,
                name=s.name,
                criticality=s.criticality,
                description=s.description,
                tier=s.tier,
                created_at=s.created_at,
            )
            for s in services
        ],
        request_id=getattr(request.state, "request_id", "req_services"),
    )


# ─── Component Ownership ───

@router.post("/ownerships", response_model=SuccessEnvelope[ComponentOwnershipResponse], summary="Assign Ownership")
def assign_ownership(
    data: ComponentOwnershipCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign fine-grained component ownership within a repository."""
    ownership = EnterpriseService.assign_ownership(db, data)
    return SuccessEnvelope(
        data=ComponentOwnershipResponse(
            id=ownership.id,
            service_id=ownership.service_id,
            repository_id=ownership.repository_id,
            component_path=ownership.component_path,
            owner_team_id=ownership.owner_team_id,
            owner_user_id=ownership.owner_user_id,
            source=ownership.source,
            created_at=ownership.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_ownership"),
    )


# ─── Cross-Repository Dependencies ───

@router.post("/dependencies", response_model=SuccessEnvelope[CrossRepoDependencyResponse], summary="Record Cross-Repo Dependency")
def record_dependency(
    data: CrossRepoDependencyCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a deterministic cross-repository dependency with provenance."""
    dep = EnterpriseService.record_cross_repo_dependency(db, data)
    return SuccessEnvelope(
        data=CrossRepoDependencyResponse(
            id=dep.id,
            organization_id=dep.organization_id,
            source_repository_id=dep.source_repository_id,
            target_repository_id=dep.target_repository_id,
            dependency_type=dep.dependency_type,
            package_or_service_name=dep.package_or_service_name,
            provenance_details=dep.provenance_details,
            created_at=dep.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_dependency"),
    )


# ─── Enterprise Graph ───

@router.get("/graph/{organization_id}", response_model=SuccessEnvelope[EnterpriseGraphResponse], summary="Get Enterprise Graph")
def get_enterprise_graph(
    organization_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Build and return the live Enterprise Software Graph for an organization."""
    graph = EnterpriseGraphService.build_enterprise_graph(db, organization_id)
    return SuccessEnvelope(
        data=graph,
        request_id=getattr(request.state, "request_id", "req_graph"),
    )


@router.get("/graph/{organization_id}/impact/{repository_id}", summary="Cross-Repo Impact Analysis")
def get_cross_repo_impact(
    organization_id: str,
    repository_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compute cross-repository blast-radius impact for a given repository."""
    impact = EnterpriseGraphService.get_cross_repo_impact(db, organization_id, repository_id)
    return SuccessEnvelope(
        data=impact,
        request_id=getattr(request.state, "request_id", "req_impact"),
    )


# ─── Historical Evidence ───

@router.post("/evidence", response_model=SuccessEnvelope[HistoricalEvidenceResponse], summary="Store Historical Evidence")
def store_evidence(
    data: HistoricalEvidenceCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store a new historical evidence record for continuous learning."""
    record = HistoricalEvidenceService.store_evidence(db, data)
    return SuccessEnvelope(
        data=HistoricalEvidenceResponse(
            id=record.id,
            organization_id=record.organization_id,
            repository_id=record.repository_id,
            evidence_type=record.evidence_type,
            title=record.title,
            content=record.content,
            provenance=record.provenance or {},
            created_at=record.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_evidence"),
    )


@router.post("/evidence/search", response_model=SuccessEnvelope[List[EvidenceSearchResult]], summary="Search Historical Evidence")
def search_evidence(
    search_request: EvidenceSearchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Perform semantic search over historical evidence using TF-IDF similarity."""
    results = HistoricalEvidenceService.search(db, search_request)
    return SuccessEnvelope(
        data=results,
        request_id=getattr(request.state, "request_id", "req_search"),
    )


# ─── Incidents ───

@router.post("/incidents", response_model=SuccessEnvelope[IncidentRecordResponse], summary="Record Incident")
def record_incident(
    data: IncidentRecordCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a production or staging incident for continuous learning."""
    from datetime import datetime, timezone
    incident = IncidentRecord(
        organization_id=data.organization_id,
        service_id=data.service_id,
        change_id=data.change_id,
        severity=data.severity.upper(),
        summary=data.summary,
        root_cause=data.root_cause,
        regression_metric=data.regression_metric,
        resolved_at=data.resolved_at,
        created_at=datetime.now(timezone.utc),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Also ingest as historical evidence for semantic search
    HistoricalEvidenceService.ingest_from_incident(
        db,
        organization_id=data.organization_id,
        incident_id=incident.id,
        summary=data.summary,
        root_cause=data.root_cause,
        severity=data.severity,
        repository_id=None,
    )

    return SuccessEnvelope(
        data=IncidentRecordResponse(
            id=incident.id,
            organization_id=incident.organization_id,
            service_id=incident.service_id,
            change_id=incident.change_id,
            severity=incident.severity,
            summary=incident.summary,
            root_cause=incident.root_cause,
            regression_metric=incident.regression_metric,
            resolved_at=incident.resolved_at,
            created_at=incident.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_incident"),
    )


# ─── Enterprise Overview ───

@router.get("/overview", response_model=SuccessEnvelope[EnterpriseOverviewResponse], summary="Enterprise Overview")
def enterprise_overview(
    request: Request,
    organization_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a high-level enterprise health and assurance overview."""
    overview = EnterpriseService.get_enterprise_overview(db, organization_id)
    return SuccessEnvelope(
        data=overview,
        request_id=getattr(request.state, "request_id", "req_overview"),
    )
