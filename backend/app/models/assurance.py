"""
Phase 3 Domain Models — AI Assurance, Invariants, Contracts, Security, Risk, Evidence & Change Proof.
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


class ChangeIntent(Base):
    """Structured representation of the intent behind a code change."""
    __tablename__ = "change_intents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    objective = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # FEATURE, BUG_FIX, REFACTOR, SECURITY, etc.
    affected_capability = Column(String(255), nullable=False)
    expected_behavior = Column(Text, nullable=True)
    affected_components = Column(JSON, nullable=True)  # List[str]
    confidence = Column(Float, nullable=False, default=0.9)
    model_info = Column(JSON, nullable=True)  # provider, model, prompt_version, latency_ms
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class BehavioralInvariant(Base):
    """Behavioral invariant that must hold true across software changes."""
    __tablename__ = "behavioral_invariants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    invariant_type = Column(String(50), nullable=False)  # DETERMINISTIC, AI_PROPOSED, HISTORICALLY_OBSERVED
    description = Column(Text, nullable=False)
    affected_component = Column(String(255), nullable=False)
    source = Column(String(100), nullable=False)
    evidence_refs = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    verification_status = Column(String(50), nullable=False, default="UNVERIFIED")  # VERIFIED, VIOLATED, UNVERIFIED
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class SemanticContract(Base):
    """Semantic API or interface contract change detection."""
    __tablename__ = "semantic_contracts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint_path = Column(String(255), nullable=False)
    http_method = Column(String(20), nullable=False)
    contract_type = Column(String(50), nullable=False)  # REST_API, SCHEMA, AUTH
    classification = Column(String(50), nullable=False)  # NO_CHANGE, COMPATIBLE_CHANGE, POTENTIALLY_BREAKING, BREAKING, UNKNOWN
    evidence_refs = Column(JSON, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class SecurityFinding(Base):
    """Explainable security risk or vulnerability finding linked to concrete evidence."""
    __tablename__ = "security_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # AUTHORIZATION_BYPASS, MISSING_AUTHENTICATION, etc.
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    affected_component = Column(String(255), nullable=False)
    evidence_refs = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=False)
    remediation_suggestion = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.9)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class TestRecommendation(Base):
    """AI-assisted candidate test recommendation covering invariants and changed contracts."""
    __tablename__ = "test_recommendations"
    __test__ = False

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    target_component = Column(String(255), nullable=False)
    test_title = Column(String(255), nullable=False)
    test_code_scaffold = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)
    invariant_covered = Column(String(255), nullable=True)
    expected_behavior = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.85)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class RiskAssessment(Base):
    """Explainable composite risk assessment combining all structural and semantic signals."""
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_risk = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    numerical_score = Column(Float, nullable=False)  # 0.0 - 100.0
    contributing_factors = Column(JSON, nullable=False)  # List of explainable factor dicts
    confidence = Column(Float, nullable=False, default=0.9)
    uncertainties = Column(JSON, nullable=True)  # List of unresolved uncertainty strings
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class EvidenceRecord(Base):
    """Unified traceable evidence unit backing assertions across the assurance pipeline."""
    __tablename__ = "evidence_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # CODE_DIFF, AST_FACT, GRAPH_RELATION, IMPACT_PATH, API_CONTRACT, TEST_RESULT, etc.
    source_reference = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class PolicyDecision(Base):
    """Deterministic governance evaluation result based on policy rules."""
    __tablename__ = "policy_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(50), nullable=False)  # PASS, WARN, BLOCK, INSUFFICIENT_EVIDENCE
    rules_evaluated = Column(JSON, nullable=False)
    blocking_reasons = Column(JSON, nullable=True)
    warning_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class ChangeProof(Base):
    """Formal verifiable Change Proof artifact documenting comprehensive assurance."""
    __tablename__ = "change_proofs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_id = Column(String(36), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    decision = Column(String(50), nullable=False)  # PASS, WARN, BLOCK, INSUFFICIENT_EVIDENCE
    risk_level = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    summary = Column(JSON, nullable=False)
    full_proof_artifact = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
