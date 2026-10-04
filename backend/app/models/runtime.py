"""
Phase 4 Domain Models — Deployments, Runtime Telemetry, Observations, Baselines, Findings & CI Gates.
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


class Deployment(Base):
    """Tracks code deployment lifecycle linked to a repository change and analysis run."""
    __tablename__ = "deployments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha = Column(String(64), nullable=False, index=True)
    environment = Column(String(50), nullable=False, default="staging")  # staging, production, canary
    status = Column(String(50), nullable=False, default="DEPLOYED")  # NOT_DEPLOYED, DEPLOYING, DEPLOYED, CANARY, ROLLED_BACK, FAILED
    deployed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    baselines = relationship("RuntimeBaseline", back_populates="deployment", cascade="all, delete-orphan")
    observations = relationship("RuntimeObservation", back_populates="deployment", cascade="all, delete-orphan")
    findings = relationship("RuntimeFinding", back_populates="deployment", cascade="all, delete-orphan")


class RuntimeBaseline(Base):
    """Pre-deployment telemetry performance baseline for comparison."""
    __tablename__ = "runtime_baselines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deployment_id = Column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False, default="*")
    request_rate = Column(Float, nullable=False, default=10.0)  # req/sec
    error_rate = Column(Float, nullable=False, default=0.5)  # percentage (e.g. 0.5% = 0.005 or 0.5)
    p50_latency_ms = Column(Float, nullable=False, default=45.0)
    p95_latency_ms = Column(Float, nullable=False, default=120.0)
    p99_latency_ms = Column(Float, nullable=False, default=220.0)
    sample_window_seconds = Column(Integer, nullable=False, default=300)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    deployment = relationship("Deployment", back_populates="baselines")


class RuntimeObservation(Base):
    """Post-deployment actual runtime telemetry sample."""
    __tablename__ = "runtime_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deployment_id = Column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False, default="*")
    request_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    error_rate = Column(Float, nullable=False, default=0.0)
    p50_latency_ms = Column(Float, nullable=False, default=0.0)
    p95_latency_ms = Column(Float, nullable=False, default=0.0)
    p99_latency_ms = Column(Float, nullable=False, default=0.0)
    status_2xx_count = Column(Integer, nullable=False, default=0)
    status_4xx_count = Column(Integer, nullable=False, default=0)
    status_5xx_count = Column(Integer, nullable=False, default=0)
    observed_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    deployment = relationship("Deployment", back_populates="observations")


class RuntimeFinding(Base):
    """Runtime assurance assertion comparing observations with baselines and predictions."""
    __tablename__ = "runtime_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deployment_id = Column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_type = Column(String(50), nullable=False)  # RUNTIME_HEALTHY, RUNTIME_REGRESSION, PERFORMANCE_REGRESSION, ERROR_RATE_REGRESSION, etc.
    severity = Column(String(50), nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    service_name = Column(String(100), nullable=False)
    endpoint_or_metric = Column(String(255), nullable=False)
    baseline_value = Column(Float, nullable=True)
    observed_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    evidence = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.95)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    deployment = relationship("Deployment", back_populates="findings")


class CIAssuranceCheck(Base):
    """Audit record for machine-readable CI/CD pipeline gate evaluations."""
    __tablename__ = "ci_assurance_checks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha = Column(String(64), nullable=False, index=True)
    gate_decision = Column(String(50), nullable=False)  # PASS, WARN, BLOCK, INSUFFICIENT_EVIDENCE
    policy_summary = Column(JSON, nullable=False)
    exit_code = Column(Integer, nullable=False, default=0)
    github_check_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
