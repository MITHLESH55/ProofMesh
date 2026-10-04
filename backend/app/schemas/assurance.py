"""
Pydantic schemas for Phase 3 — AI Assurance, Invariants, Contracts, Security, Risk, Evidence, and Change Proofs.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Change Intent ---

class ChangeIntentResponse(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    objective: str
    category: str
    affected_capability: str
    expected_behavior: Optional[str] = None
    affected_components: List[str] = Field(default_factory=list)
    confidence: float = 0.9
    model_info: Optional[Dict[str, Any]] = None
    created_at: datetime


# --- Behavioral Invariants ---

class BehavioralInvariantResponse(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    invariant_type: str  # DETERMINISTIC, AI_PROPOSED, HISTORICALLY_OBSERVED
    description: str
    affected_component: str
    source: str
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    verification_status: str  # VERIFIED, VIOLATED, UNVERIFIED
    created_at: datetime


# --- Semantic Contracts ---

class SemanticContractResponse(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    endpoint_path: str
    http_method: str
    contract_type: str
    classification: str  # NO_CHANGE, COMPATIBLE_CHANGE, POTENTIALLY_BREAKING, BREAKING, UNKNOWN
    evidence_refs: List[str] = Field(default_factory=list)
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


# --- Security Findings ---

class SecurityFindingResponse(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    category: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    affected_component: str
    evidence_refs: List[str] = Field(default_factory=list)
    reasoning: str
    remediation_suggestion: Optional[str] = None
    confidence: float = 0.9
    created_at: datetime


# --- Test Recommendations ---

class TestRecommendationResponse(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    target_component: str
    test_title: str
    test_code_scaffold: Optional[str] = None
    reason: str
    invariant_covered: Optional[str] = None
    expected_behavior: Optional[str] = None
    confidence: float = 0.85
    created_at: datetime


# --- Risk Assessment ---

class ContributingFactor(BaseModel):
    name: str
    weight: float
    description: str
    evidence_ref: Optional[str] = None


class RiskAssessmentResponse(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    overall_risk: str  # LOW, MEDIUM, HIGH, CRITICAL
    numerical_score: float  # 0.0 - 100.0
    contributing_factors: List[ContributingFactor] = Field(default_factory=list)
    confidence: float = 0.9
    uncertainties: List[str] = Field(default_factory=list)
    created_at: datetime


# --- Evidence Records ---

class EvidenceRecordResponse(BaseModel):
    id: str
    analysis_run_id: str
    source_type: str  # CODE_DIFF, AST_FACT, GRAPH_RELATION, IMPACT_PATH, API_CONTRACT, etc.
    source_reference: str
    confidence: float = 1.0
    explanation: str
    created_at: datetime


# --- Policy Decisions ---

class PolicyDecisionResponse(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    decision: str  # PASS, WARN, BLOCK, INSUFFICIENT_EVIDENCE
    rules_evaluated: List[Dict[str, Any]] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)
    warning_reasons: List[str] = Field(default_factory=list)
    created_at: datetime


class PolicyEvaluationRequest(BaseModel):
    policy_overrides: Optional[Dict[str, Any]] = None


# --- Change Proof ---

class ChangeProofResponse(BaseModel):
    id: str
    change_id: str
    analysis_run_id: str
    decision: str  # PASS, WARN, BLOCK, INSUFFICIENT_EVIDENCE
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    summary: Dict[str, Any]
    full_proof_artifact: Dict[str, Any]
    created_at: datetime


# --- Complete Assurance Overview ---

class AssuranceOverviewResponse(BaseModel):
    analysis_run_id: str
    change_id: str
    status: str
    intent: Optional[ChangeIntentResponse] = None
    invariants: List[BehavioralInvariantResponse] = Field(default_factory=list)
    contracts: List[SemanticContractResponse] = Field(default_factory=list)
    security_findings: List[SecurityFindingResponse] = Field(default_factory=list)
    test_recommendations: List[TestRecommendationResponse] = Field(default_factory=list)
    risk: Optional[RiskAssessmentResponse] = None
    evidence: List[EvidenceRecordResponse] = Field(default_factory=list)
    policy_decision: Optional[PolicyDecisionResponse] = None
    proof: Optional[ChangeProofResponse] = None
