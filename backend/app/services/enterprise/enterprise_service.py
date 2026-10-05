"""
Enterprise Service Management.

Handles enterprise teams, microservices, component ownership, criticality mapping,
cross-repository dependencies, and high-level enterprise health overviews.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.entities import Organization, Repository, User
from app.models.enterprise import Team, Service, ComponentOwnership, CrossRepoDependency, IncidentRecord
from app.models.agent import AgentDefinition
from app.schemas.enterprise import (
    TeamCreate,
    ServiceCreate,
    ComponentOwnershipCreate,
    CrossRepoDependencyCreate,
    EnterpriseOverviewResponse,
)


class EnterpriseService:
    """Enterprise multi-repository, service ownership, and dependency management."""

    @staticmethod
    def create_team(db: Session, data: TeamCreate) -> Team:
        team = Team(
            organization_id=data.organization_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
            created_at=datetime.now(timezone.utc),
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def list_teams(db: Session, organization_id: Optional[str] = None) -> List[Team]:
        query = db.query(Team)
        if organization_id:
            query = query.filter(Team.organization_id == organization_id)
        return query.order_by(Team.name.asc()).all()

    @staticmethod
    def create_service(db: Session, data: ServiceCreate) -> Service:
        service = Service(
            organization_id=data.organization_id,
            team_id=data.team_id,
            repository_id=data.repository_id,
            name=data.name,
            criticality=data.criticality.upper(),
            description=data.description,
            tier=data.tier,
            created_at=datetime.now(timezone.utc),
        )
        db.add(service)
        db.commit()
        db.refresh(service)
        return service

    @staticmethod
    def list_services(db: Session, organization_id: Optional[str] = None, criticality: Optional[str] = None) -> List[Service]:
        query = db.query(Service)
        if organization_id:
            query = query.filter(Service.organization_id == organization_id)
        if criticality:
            query = query.filter(Service.criticality == criticality.upper())
        return query.order_by(Service.name.asc()).all()

    @staticmethod
    def assign_ownership(db: Session, data: ComponentOwnershipCreate) -> ComponentOwnership:
        ownership = ComponentOwnership(
            service_id=data.service_id,
            repository_id=data.repository_id,
            component_path=data.component_path,
            owner_team_id=data.owner_team_id,
            owner_user_id=data.owner_user_id,
            source=data.source,
            created_at=datetime.now(timezone.utc),
        )
        db.add(ownership)
        db.commit()
        db.refresh(ownership)
        return ownership

    @staticmethod
    def list_ownerships(db: Session, repository_id: Optional[str] = None, service_id: Optional[str] = None) -> List[ComponentOwnership]:
        query = db.query(ComponentOwnership)
        if repository_id:
            query = query.filter(ComponentOwnership.repository_id == repository_id)
        if service_id:
            query = query.filter(ComponentOwnership.service_id == service_id)
        return query.all()

    @staticmethod
    def record_cross_repo_dependency(db: Session, data: CrossRepoDependencyCreate) -> CrossRepoDependency:
        dep = CrossRepoDependency(
            organization_id=data.organization_id,
            source_repository_id=data.source_repository_id,
            target_repository_id=data.target_repository_id,
            dependency_type=data.dependency_type.upper(),
            package_or_service_name=data.package_or_service_name,
            provenance_details=data.provenance_details,
            created_at=datetime.now(timezone.utc),
        )
        db.add(dep)
        db.commit()
        db.refresh(dep)
        return dep

    @staticmethod
    def list_cross_repo_dependencies(db: Session, organization_id: Optional[str] = None) -> List[CrossRepoDependency]:
        query = db.query(CrossRepoDependency)
        if organization_id:
            query = query.filter(CrossRepoDependency.organization_id == organization_id)
        return query.all()

    @staticmethod
    def get_enterprise_overview(db: Session, organization_id: Optional[str] = None) -> EnterpriseOverviewResponse:
        orgs_count = db.query(Organization).count()
        teams_q = db.query(Team)
        repos_q = db.query(Repository)
        services_q = db.query(Service)
        deps_q = db.query(CrossRepoDependency)
        incidents_q = db.query(IncidentRecord)
        agents_q = db.query(AgentDefinition)

        if organization_id:
            teams_q = teams_q.filter(Team.organization_id == organization_id)
            repos_q = repos_q.filter(Repository.organization_id == organization_id)
            services_q = services_q.filter(Service.organization_id == organization_id)
            deps_q = deps_q.filter(CrossRepoDependency.organization_id == organization_id)
            incidents_q = incidents_q.filter(IncidentRecord.organization_id == organization_id)
            agents_q = agents_q.filter(AgentDefinition.organization_id == organization_id)

        all_services = services_q.all()
        critical_count = sum(1 for s in all_services if s.criticality == "CRITICAL")
        active_incidents = incidents_q.filter(IncidentRecord.resolved_at.is_(None)).count()
        active_agents = agents_q.filter(AgentDefinition.status == "ACTIVE").count()

        return EnterpriseOverviewResponse(
            total_organizations=orgs_count,
            total_teams=teams_q.count(),
            total_repositories=repos_q.count(),
            total_services=len(all_services),
            critical_services_count=critical_count,
            total_cross_repo_deps=deps_q.count(),
            active_incidents_count=active_incidents,
            active_agents_count=active_agents,
        )
