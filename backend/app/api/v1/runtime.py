"""
Runtime Observability & Extended Change Proof Router.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.entities import User
from app.models.runtime import RuntimeFinding
from app.schemas.common import SuccessEnvelope
from app.schemas.runtime import (
    RuntimeFindingResponse,
    RuntimeMetricsSummaryResponse,
    RuntimeServiceHealthResponse,
    ExtendedChangeProofResponse,
)
from app.services.auth.service import get_current_user
from app.services.runtime.telemetry_service import TelemetryService
from app.services.runtime.runtime_assurance_engine import RuntimeAssuranceEngine

router = APIRouter(tags=["Runtime Assurance"])


@router.get("/runtime/services", response_model=SuccessEnvelope[List[RuntimeServiceHealthResponse]])
def get_runtime_services(
    request: Request,
    deployment_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    summary = TelemetryService.get_metrics_summary(db, deployment_id=deployment_id)
    return SuccessEnvelope(
        data=summary.services,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/runtime/metrics", response_model=SuccessEnvelope[RuntimeMetricsSummaryResponse])
def get_runtime_metrics(
    request: Request,
    deployment_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    summary = TelemetryService.get_metrics_summary(db, deployment_id=deployment_id)
    return SuccessEnvelope(
        data=summary,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/runtime/findings", response_model=SuccessEnvelope[List[RuntimeFindingResponse]])
def list_runtime_findings(
    request: Request,
    deployment_id: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(RuntimeFinding)
    if deployment_id:
        query = query.filter(RuntimeFinding.deployment_id == deployment_id)
    if severity:
        query = query.filter(RuntimeFinding.severity == severity)
    
    findings = query.order_by(RuntimeFinding.created_at.desc()).all()
    return SuccessEnvelope(
        data=[
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
            )
            for f in findings
        ],
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/changes/{change_id}/runtime", response_model=SuccessEnvelope[ExtendedChangeProofResponse])
def get_change_runtime_proof(
    change_id: str,
    request: Request,
    deployment_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    extended_proof = RuntimeAssuranceEngine.build_extended_change_proof(
        db, change_id=change_id, deployment_id=deployment_id
    )
    return SuccessEnvelope(
        data=extended_proof,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )
