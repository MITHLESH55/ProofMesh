"""
Phase 5 Enterprise Domain Models — Teams, Services, Ownership, Criticality, Cross-Repo Dependencies, Historical Evidence, Incidents.
"""
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Team(Base):
    """Enterprise engineering team entity."""
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    services = relationship("Service", back_populates="team", cascade="all, delete-orphan")


class Service(Base):
    """Enterprise microservice or component with ownership and criticality."""
    __tablename__ = "services"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    criticality = Column(String(50), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=True)
    tier = Column(Integer, nullable=False, default=2)  # Tier 1 (Mission Critical), Tier 2, Tier 3
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    team = relationship("Team", back_populates="services")
    ownerships = relationship("ComponentOwnership", back_populates="service", cascade="all, delete-orphan")
    incidents = relationship("IncidentRecord", back_populates="service", cascade="all, delete-orphan")


class ComponentOwnership(Base):
    """Fine-grained component ownership tracking (CODEOWNERS / explicit metadata)."""
    __tablename__ = "component_ownerships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=True, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    component_path = Column(String(255), nullable=False)  # e.g., "auth/", "pkg/crypto/*", "api/v1/*"
    owner_team_id = Column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    owner_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    source = Column(String(50), nullable=False, default="EXPLICIT")  # CODEOWNERS, CONFIG, EXPLICIT
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    service = relationship("Service", back_populates="ownerships")


class CrossRepoDependency(Base):
    """Deterministic cross-repository dependency relationship."""
    __tablename__ = "cross_repo_dependencies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    target_repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type = Column(String(50), nullable=False)  # PACKAGE, API_CALL, EVENT_STREAM, SHARED_LIB
    package_or_service_name = Column(String(100), nullable=False)
    provenance_details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class EnterpriseGraphVersion(Base):
    """Temporal snapshot metadata for enterprise dependency graph."""
    __tablename__ = "enterprise_graph_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    version_tag = Column(String(100), nullable=False)
    commit_sha = Column(String(64), nullable=False)
    graph_snapshot_ref = Column(String(255), nullable=True)
    node_count = Column(Integer, nullable=False, default=0)
    edge_count = Column(Integer, nullable=False, default=0)
    analyzed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class HistoricalEvidence(Base):
    """Knowledge base record of historical change proofs, incidents, and regressions for semantic search."""
    __tablename__ = "historical_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, index=True)
    evidence_type = Column(String(50), nullable=False)  # PROOF_SUMMARY, INCIDENT, REGRESSION, REMEDIATION, TEST_RATIONALE
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Stored as embedding vector list or token weights
    provenance = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class IncidentRecord(Base):
    """Record of historical production/staging incident for continuous learning."""
    __tablename__ = "incident_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=True, index=True)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="SET NULL"), nullable=True, index=True)
    severity = Column(String(50), nullable=False, default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    summary = Column(String(255), nullable=False)
    root_cause = Column(Text, nullable=False)
    regression_metric = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    service = relationship("Service", back_populates="incidents")
