"""
Pydantic schemas for Phase 4 — Deployments, Telemetry, Baselines, Runtime Observations, Findings, and CI Gates.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Deployment Schemas ---

class DeploymentCreate(BaseModel):
    repository_id: str
    change_id: str
    analysis_run_id: str
    commit_sha: str
    environment: str = "staging"
    status: str = "DEPLOYED"


class DeploymentResponse(BaseModel):
    id: str
    repository_id: str
    change_id: str
    analysis_run_id: str
    commit_sha: str
    environment: str
    status: str
    deployed_at: datetime
    created_at: datetime


class DeploymentListResponse(BaseModel):
    total: int
    items: List[DeploymentResponse]


# --- Runtime Baseline Schemas ---

class RuntimeBaselineCreate(BaseModel):
    deployment_id: str
    service_name: str
    endpoint: str = "*"
    request_rate: float = 10.0
    error_rate: float = 0.5  # percentage (e.g. 0.5%)
    p50_latency_ms: float = 45.0
    p95_latency_ms: float = 120.0
    p99_latency_ms: float = 220.0
    sample_window_seconds: int = 300


class RuntimeBaselineResponse(BaseModel):
    id: str
    deployment_id: str
    service_name: str
    endpoint: str
    request_rate: float
    error_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    sample_window_seconds: int
    created_at: datetime


# --- Runtime Observation Schemas ---

class RuntimeObservationCreate(BaseModel):
    deployment_id: str
    service_name: str
    endpoint: str = "*"
    request_count: int = 0
    error_count: int = 0
    error_rate: float = 0.0  # percentage
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    status_2xx_count: int = 0
    status_4xx_count: int = 0
    status_5xx_count: int = 0


class RuntimeObservationResponse(BaseModel):
    id: str
    deployment_id: str
    service_name: str
    endpoint: str
    request_count: int
    error_count: int
    error_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    status_2xx_count: int
    status_4xx_count: int
    status_5xx_count: int
    observed_at: datetime


# --- Runtime Finding Schemas ---

class RuntimeFindingResponse(BaseModel):
    id: str
    deployment_id: str
    finding_type: str  # RUNTIME_HEALTHY, RUNTIME_REGRESSION, PERFORMANCE_REGRESSION, ERROR_RATE_REGRESSION, SERVICE_DEGRADATION, TRAFFIC_ANOMALY, INSUFFICIENT_RUNTIME_EVIDENCE
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    service_name: str
    endpoint_or_metric: str
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    threshold_value: Optional[float] = None
    evidence: str
    confidence: float = 0.95
    created_at: datetime


# --- Prediction vs Observed Schemas ---

class ComponentTrafficStatus(BaseModel):
    service_name: str
    predicted_impacted: bool
    observed_traffic: bool
    observed_error_rate: float
    observed_p95_ms: float
    status: str  # MATCH, UNEXPECTED_TRAFFIC, UNEXPECTED_QUIET, REGRESSION


class PredictionVsObservedReport(BaseModel):
    deployment_id: str
    change_id: str
    predicted_services: List[str]
    observed_services: List[str]
    components: List[ComponentTrafficStatus]
    summary_match: bool
    discrepancies: List[str] = Field(default_factory=list)


# --- CI Assurance Schemas ---

class CIAssuranceCheckRequest(BaseModel):
    change_id: str
    commit_sha: Optional[str] = None
    fail_on_warn: bool = False
    publish_github_check: bool = False


class CIAssuranceCheckResponse(BaseModel):
    id: str
    change_id: str
    commit_sha: str
    gate_decision: str  # PASS, WARN, BLOCK, INSUFFICIENT_EVIDENCE
    risk_level: str
    critical_findings: List[str]
    warning_findings: List[str]
    policy_summary: Dict[str, Any]
    exit_code: int
    github_check_id: Optional[str] = None
    proof_url: str
    created_at: datetime


# --- Extended Change Proof & Runtime Overview ---

class ExtendedChangeProofResponse(BaseModel):
    change_id: str
    analysis_run_id: str
    deployment_id: Optional[str] = None
    phase3_decision: str
    runtime_decision: str  # RUNTIME_VERIFIED, RUNTIME_WARNING, RUNTIME_REGRESSION, INSUFFICIENT_RUNTIME_EVIDENCE
    risk_level: str
    deployment_evidence: Optional[Dict[str, Any]] = None
    runtime_evidence: Optional[Dict[str, Any]] = None
    prediction_vs_observed: Optional[PredictionVsObservedReport] = None
    runtime_findings: List[RuntimeFindingResponse] = Field(default_factory=list)
    final_combined_verdict: str  # e.g., VERIFIED_SAFE, BLOCKED, RUNTIME_REGRESSION_DETECTED
    auditable_record: Dict[str, Any]
    created_at: datetime


class RuntimeServiceHealthResponse(BaseModel):
    service_name: str
    status: str  # HEALTHY, DEGRADED, FAILING, UNKNOWN
    request_rate: float
    error_rate: float
    p95_latency_ms: float
    last_seen: Optional[datetime] = None


class RuntimeMetricsSummaryResponse(BaseModel):
    deployment_id: Optional[str] = None
    total_requests: int
    total_errors: int
    overall_error_rate: float
    avg_p95_latency_ms: float
    services: List[RuntimeServiceHealthResponse]
    findings_count: Dict[str, int]
