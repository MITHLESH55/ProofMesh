"""
Deployments API Router.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.entities import User
from app.models.runtime import Deployment
from app.schemas.common import SuccessEnvelope
from app.schemas.runtime import (
    DeploymentCreate,
    DeploymentResponse,
    RuntimeBaselineCreate,
    RuntimeBaselineResponse,
    RuntimeObservationCreate,
    RuntimeObservationResponse,
    RuntimeFindingResponse,
    PredictionVsObservedReport,
)
from app.services.auth.service import get_current_user
from app.services.runtime.telemetry_service import TelemetryService
from app.services.runtime.runtime_assurance_engine import RuntimeAssuranceEngine
from app.services.runtime.prediction_matcher import PredictionMatcher

router = APIRouter(prefix="/deployments", tags=["Deployments"])


@router.post("", response_model=SuccessEnvelope[DeploymentResponse], status_code=status.HTTP_201_CREATED)
def create_deployment(
    payload: DeploymentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dep = TelemetryService.create_deployment(db, payload)
    return SuccessEnvelope(
        data=DeploymentResponse(
            id=dep.id,
            repository_id=dep.repository_id,
            change_id=dep.change_id,
            analysis_run_id=dep.analysis_run_id,
            commit_sha=dep.commit_sha,
            environment=dep.environment,
            status=dep.status,
            deployed_at=dep.deployed_at,
            created_at=dep.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("", response_model=SuccessEnvelope[List[DeploymentResponse]])
def list_deployments(
    request: Request,
    repository_id: Optional[str] = None,
    change_id: Optional[str] = None,
    environment: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = TelemetryService.list_deployments(
        db, repository_id=repository_id, change_id=change_id, environment=environment, limit=limit, offset=offset
    )
    return SuccessEnvelope(
        data=[
            DeploymentResponse(
                id=d.id,
                repository_id=d.repository_id,
                change_id=d.change_id,
                analysis_run_id=d.analysis_run_id,
                commit_sha=d.commit_sha,
                environment=d.environment,
                status=d.status,
                deployed_at=d.deployed_at,
                created_at=d.created_at,
            )
            for d in items
        ],
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/{deployment_id}", response_model=SuccessEnvelope[DeploymentResponse])
def get_deployment(
    deployment_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dep = TelemetryService.get_deployment(db, deployment_id)
    if not dep:
        raise NotFoundError("Deployment not found")
    return SuccessEnvelope(
        data=DeploymentResponse(
            id=dep.id,
            repository_id=dep.repository_id,
            change_id=dep.change_id,
            analysis_run_id=dep.analysis_run_id,
            commit_sha=dep.commit_sha,
            environment=dep.environment,
            status=dep.status,
            deployed_at=dep.deployed_at,
            created_at=dep.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/{deployment_id}/runtime", response_model=SuccessEnvelope[Dict[str, Any]])
def get_deployment_runtime(
    deployment_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dep = TelemetryService.get_deployment(db, deployment_id)
    if not dep:
        raise NotFoundError("Deployment not found")

    baselines = TelemetryService.get_baselines(db, deployment_id)
    observations = TelemetryService.get_observations(db, deployment_id)

    return SuccessEnvelope(
        data={
            "deployment_id": deployment_id,
            "baselines": [
                RuntimeBaselineResponse(
                    id=b.id,
                    deployment_id=b.deployment_id,
                    service_name=b.service_name,
                    endpoint=b.endpoint,
                    request_rate=b.request_rate,
                    error_rate=b.error_rate,
                    p50_latency_ms=b.p50_latency_ms,
                    p95_latency_ms=b.p95_latency_ms,
                    p99_latency_ms=b.p99_latency_ms,
                    sample_window_seconds=b.sample_window_seconds,
                    created_at=b.created_at,
                ).model_dump()
                for b in baselines
            ],
            "observations": [
                RuntimeObservationResponse(
                    id=o.id,
                    deployment_id=o.deployment_id,
                    service_name=o.service_name,
                    endpoint=o.endpoint,
                    request_count=o.request_count,
                    error_count=o.error_count,
                    error_rate=o.error_rate,
                    p50_latency_ms=o.p50_latency_ms,
                    p95_latency_ms=o.p95_latency_ms,
                    p99_latency_ms=o.p99_latency_ms,
                    status_2xx_count=o.status_2xx_count,
                    status_4xx_count=o.status_4xx_count,
                    status_5xx_count=o.status_5xx_count,
                    observed_at=o.observed_at,
                ).model_dump()
                for o in observations
            ],
        },
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/{deployment_id}/assurance", response_model=SuccessEnvelope[Dict[str, Any]])
def get_deployment_assurance(
    deployment_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dep = TelemetryService.get_deployment(db, deployment_id)
    if not dep:
        raise NotFoundError("Deployment not found")

    findings = RuntimeAssuranceEngine.evaluate_runtime_assurance(db, dep)
    decision = RuntimeAssuranceEngine.determine_runtime_decision(findings)
    pred_report = PredictionMatcher.compare_prediction_vs_observed(db, dep)

    return SuccessEnvelope(
        data={
            "deployment_id": deployment_id,
            "runtime_decision": decision,
            "findings": [
                RuntimeFindingResponse(
                    id=f.id,
                    deployment_id=f.deployment_id,
                    finding_type=f.finding_type,
                    severity=f.severity,
                    service_name=f.service_name,
                    endpoint_or_metric=f.endpoint_or_metric,
                    baseline_value=f.baseline_value,
                    observed_value=f.observed_value,
                    threshold_value=f.threshold_value,
                    evidence=f.evidence,
                    confidence=f.confidence,
                    created_at=f.created_at,
                ).model_dump()
                for f in findings
            ],
            "prediction_vs_observed": pred_report.model_dump(),
        },
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.post("/{deployment_id}/observations", response_model=SuccessEnvelope[RuntimeObservationResponse], status_code=status.HTTP_201_CREATED)
def record_observation(
    deployment_id: str,
    payload: RuntimeObservationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dep = TelemetryService.get_deployment(db, deployment_id)
    if not dep:
        raise NotFoundError("Deployment not found")

    payload.deployment_id = deployment_id
    obs = TelemetryService.record_observation(db, payload)
    return SuccessEnvelope(
        data=RuntimeObservationResponse(
            id=obs.id,
            deployment_id=obs.deployment_id,
            service_name=obs.service_name,
            endpoint=obs.endpoint,
            request_count=obs.request_count,
            error_count=obs.error_count,
            error_rate=obs.error_rate,
            p50_latency_ms=obs.p50_latency_ms,
            p95_latency_ms=obs.p95_latency_ms,
            p99_latency_ms=obs.p99_latency_ms,
            status_2xx_count=obs.status_2xx_count,
            status_4xx_count=obs.status_4xx_count,
            status_5xx_count=obs.status_5xx_count,
            observed_at=obs.observed_at,
        ),
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.post("/{deployment_id}/baselines", response_model=SuccessEnvelope[RuntimeBaselineResponse], status_code=status.HTTP_201_CREATED)
def record_baseline(
    deployment_id: str,
    payload: RuntimeBaselineCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dep = TelemetryService.get_deployment(db, deployment_id)
    if not dep:
        raise NotFoundError("Deployment not found")

    payload.deployment_id = deployment_id
    base = TelemetryService.record_baseline(db, payload)
    return SuccessEnvelope(
        data=RuntimeBaselineResponse(
            id=base.id,
            deployment_id=base.deployment_id,
            service_name=base.service_name,
            endpoint=base.endpoint,
            request_rate=base.request_rate,
            error_rate=base.error_rate,
            p50_latency_ms=base.p50_latency_ms,
            p95_latency_ms=base.p95_latency_ms,
            p99_latency_ms=base.p99_latency_ms,
            sample_window_seconds=base.sample_window_seconds,
            created_at=base.created_at,
        ),
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )
