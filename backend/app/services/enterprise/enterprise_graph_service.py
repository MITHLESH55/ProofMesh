"""
Enterprise Graph Service.

Constructs and manages the Enterprise Software Graph — a cross-repository
dependency graph connecting repositories, services, teams, and their
relationships for organization-wide impact analysis and risk propagation.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.entities import Organization, Repository
from app.models.enterprise import (
    Team,
    Service,
    CrossRepoDependency,
    EnterpriseGraphVersion,
    ComponentOwnership,
)
from app.schemas.enterprise import (
    EnterpriseGraphNode,
    EnterpriseGraphEdge,
    EnterpriseGraphResponse,
    EnterpriseGraphVersionResponse,
)


class EnterpriseGraphService:
    """Builds and queries the Enterprise Software Graph for cross-repo impact analysis."""

    @staticmethod
    def build_enterprise_graph(
        db: Session, organization_id: str
    ) -> EnterpriseGraphResponse:
        """
        Construct the live enterprise dependency graph for an organization.

        Nodes represent: repositories, services, teams.
        Edges represent: ownership, cross-repo dependencies, team-service mappings.
        """
        # Fetch entities
        repos = db.query(Repository).filter(Repository.organization_id == organization_id).all()
        services = db.query(Service).filter(Service.organization_id == organization_id).all()
        teams = db.query(Team).filter(Team.organization_id == organization_id).all()
        cross_deps = db.query(CrossRepoDependency).filter(
            CrossRepoDependency.organization_id == organization_id
        ).all()
        ownerships = db.query(ComponentOwnership).join(Service).filter(
            Service.organization_id == organization_id
        ).all()

        nodes: List[EnterpriseGraphNode] = []
        edges: List[EnterpriseGraphEdge] = []
        node_ids_seen = set()

        # Add repository nodes
        for repo in repos:
            if repo.id not in node_ids_seen:
                nodes.append(EnterpriseGraphNode(
                    id=repo.id,
                    label=repo.full_name or repo.name,
                    type="REPOSITORY",
                    metadata={"name": repo.name, "default_branch": getattr(repo, "default_branch", "main")},
                ))
                node_ids_seen.add(repo.id)

        # Add service nodes
        for svc in services:
            if svc.id not in node_ids_seen:
                nodes.append(EnterpriseGraphNode(
                    id=svc.id,
                    label=svc.name,
                    type="SERVICE",
                    criticality=svc.criticality,
                    metadata={"tier": svc.tier, "description": svc.description or ""},
                ))
                node_ids_seen.add(svc.id)
                # Link service → repository
                if svc.repository_id and svc.repository_id in node_ids_seen:
                    edges.append(EnterpriseGraphEdge(
                        source=svc.id,
                        target=svc.repository_id,
                        type="DEPLOYED_FROM",
                        metadata={"criticality": svc.criticality},
                    ))

        # Add team nodes and ownership edges
        for team in teams:
            if team.id not in node_ids_seen:
                nodes.append(EnterpriseGraphNode(
                    id=team.id,
                    label=team.name,
                    type="TEAM",
                    metadata={"slug": team.slug, "description": team.description or ""},
                ))
                node_ids_seen.add(team.id)

        # Team → Service ownership edges
        for svc in services:
            if svc.team_id and svc.team_id in node_ids_seen and svc.id in node_ids_seen:
                edges.append(EnterpriseGraphEdge(
                    source=svc.team_id,
                    target=svc.id,
                    type="OWNS",
                    metadata={},
                ))

        # Cross-repository dependency edges
        for dep in cross_deps:
            if dep.source_repository_id in node_ids_seen and dep.target_repository_id in node_ids_seen:
                edges.append(EnterpriseGraphEdge(
                    source=dep.source_repository_id,
                    target=dep.target_repository_id,
                    type=dep.dependency_type,
                    metadata={
                        "package_or_service": dep.package_or_service_name,
                        "provenance": dep.provenance_details,
                    },
                ))

        # Component ownership edges
        for own in ownerships:
            if own.owner_team_id and own.owner_team_id in node_ids_seen and own.repository_id in node_ids_seen:
                edges.append(EnterpriseGraphEdge(
                    source=own.owner_team_id,
                    target=own.repository_id,
                    type="OWNS_COMPONENT",
                    metadata={"component_path": own.component_path, "source": own.source},
                ))

        return EnterpriseGraphResponse(
            organization_id=organization_id,
            nodes=nodes,
            edges=edges,
            total_services=len(services),
            total_repositories=len(repos),
        )

    @staticmethod
    def snapshot_graph(
        db: Session,
        organization_id: str,
        version_tag: str,
        commit_sha: str,
    ) -> EnterpriseGraphVersion:
        """Create a temporal snapshot reference for the current enterprise graph state."""
        graph = EnterpriseGraphService.build_enterprise_graph(db, organization_id)

        version = EnterpriseGraphVersion(
            organization_id=organization_id,
            version_tag=version_tag,
            commit_sha=commit_sha,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            analyzed_at=datetime.now(timezone.utc),
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return version

    @staticmethod
    def list_graph_versions(
        db: Session, organization_id: str, limit: int = 20
    ) -> List[EnterpriseGraphVersion]:
        """List historical graph snapshots for an organization."""
        return (
            db.query(EnterpriseGraphVersion)
            .filter(EnterpriseGraphVersion.organization_id == organization_id)
            .order_by(EnterpriseGraphVersion.analyzed_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_cross_repo_impact(
        db: Session,
        organization_id: str,
        repository_id: str,
    ) -> Dict[str, Any]:
        """
        Compute cross-repository impact analysis for a single repository.

        Returns all repositories, services, and teams that are upstream or downstream
        dependents, enabling blast-radius estimation at the enterprise level.
        """
        # Find downstream (repositories that depend on this one)
        downstream_deps = (
            db.query(CrossRepoDependency)
            .filter(
                CrossRepoDependency.organization_id == organization_id,
                CrossRepoDependency.target_repository_id == repository_id,
            )
            .all()
        )
        downstream_repo_ids = [d.source_repository_id for d in downstream_deps]

        # Find upstream (repositories this one depends on)
        upstream_deps = (
            db.query(CrossRepoDependency)
            .filter(
                CrossRepoDependency.organization_id == organization_id,
                CrossRepoDependency.source_repository_id == repository_id,
            )
            .all()
        )
        upstream_repo_ids = [d.target_repository_id for d in upstream_deps]

        # Find affected services
        affected_services = (
            db.query(Service)
            .filter(
                Service.organization_id == organization_id,
                Service.repository_id.in_(downstream_repo_ids + [repository_id]),
            )
            .all()
        )

        # Find affected teams
        affected_team_ids = set()
        for svc in affected_services:
            if svc.team_id:
                affected_team_ids.add(svc.team_id)

        affected_teams = []
        if affected_team_ids:
            affected_teams = (
                db.query(Team)
                .filter(Team.id.in_(affected_team_ids))
                .all()
            )

        return {
            "repository_id": repository_id,
            "organization_id": organization_id,
            "downstream_repository_count": len(downstream_repo_ids),
            "downstream_repository_ids": downstream_repo_ids,
            "upstream_repository_count": len(upstream_repo_ids),
            "upstream_repository_ids": upstream_repo_ids,
            "affected_services": [
                {
                    "id": s.id,
                    "name": s.name,
                    "criticality": s.criticality,
                    "tier": s.tier,
                }
                for s in affected_services
            ],
            "affected_teams": [
                {"id": t.id, "name": t.name, "slug": t.slug}
                for t in affected_teams
            ],
            "max_criticality": max(
                (s.criticality for s in affected_services),
                default="NONE",
                key=lambda c: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}.get(c, 0),
            ),
        }
