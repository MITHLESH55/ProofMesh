"""
Runtime Assurance Engine.

Executes deterministic regression analysis comparing runtime telemetry with pre-deployment
baselines, generates structured runtime findings, and builds the Extended Change Proof.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.runtime import Deployment, RuntimeBaseline, RuntimeObservation, RuntimeFinding
from app.models.assurance import ChangeProof, PolicyDecision, RiskAssessment
from app.schemas.runtime import (
    RuntimeFindingResponse,
    ExtendedChangeProofResponse,
    PredictionVsObservedReport,
)
from app.services.runtime.prediction_matcher import PredictionMatcher


class RuntimeAssuranceEngine:
    """Deterministic runtime regression detection and extended proof synthesis."""

    # Default Assurance Thresholds
    MAX_ALLOWED_ERROR_RATE_PERCENT: float = 2.0
    ERROR_RATE_INCREASE_MULTIPLIER: float = 2.5
    MAX_P95_LATENCY_MS: float = 350.0
    LATENCY_INCREASE_MULTIPLIER: float = 1.75
    MAX_ALLOWED_5XX_PERCENT: float = 1.0

    @classmethod
    def evaluate_runtime_assurance(
        cls,
        db: Session,
        deployment: Deployment,
        predicted_services: Optional[List[str]] = None,
    ) -> List[RuntimeFinding]:
        """
        Compare observations against baselines deterministically and persist findings.
        """
        # Clear existing findings for this deployment to allow idempotent re-evaluation
        db.query(RuntimeFinding).filter(RuntimeFinding.deployment_id == deployment.id).delete()

        observations = db.query(RuntimeObservation).filter(
            RuntimeObservation.deployment_id == deployment.id
        ).all()
        baselines = db.query(RuntimeBaseline).filter(
            RuntimeBaseline.deployment_id == deployment.id
        ).all()
        baseline_map: Dict[str, RuntimeBaseline] = {b.service_name: b for b in baselines}

        findings: List[RuntimeFinding] = []

        if not observations:
            insufficient_finding = RuntimeFinding(
                deployment_id=deployment.id,
                finding_type="INSUFFICIENT_RUNTIME_EVIDENCE",
                severity="HIGH",
                service_name="all",
                endpoint_or_metric="traffic",
                baseline_value=None,
                observed_value=0.0,
                threshold_value=1.0,
                evidence="No runtime telemetry observations received for this deployment yet.",
                confidence=0.99,
                created_at=datetime.now(timezone.utc),
            )
            db.add(insufficient_finding)
            db.commit()
            db.refresh(insufficient_finding)
            return [insufficient_finding]

        for obs in observations:
            b = baseline_map.get(obs.service_name)
            base_err_rate = b.error_rate if b else 0.5
            base_p95 = b.p95_latency_ms if b else 120.0

            # 1. Error Rate Regression Check
            err_spike = obs.error_rate > (base_err_rate * cls.ERROR_RATE_INCREASE_MULTIPLIER) and obs.error_rate > 1.0
            err_absolute = obs.error_rate > cls.MAX_ALLOWED_ERROR_RATE_PERCENT

            if err_spike or err_absolute:
                sev = "CRITICAL" if obs.error_rate > 5.0 else "HIGH"
                f = RuntimeFinding(
                    deployment_id=deployment.id,
                    finding_type="ERROR_RATE_REGRESSION",
                    severity=sev,
                    service_name=obs.service_name,
                    endpoint_or_metric=f"{obs.endpoint} (error_rate)",
                    baseline_value=base_err_rate,
                    observed_value=obs.error_rate,
                    threshold_value=min(cls.MAX_ALLOWED_ERROR_RATE_PERCENT, base_err_rate * cls.ERROR_RATE_INCREASE_MULTIPLIER),
                    evidence=(
                        f"Observed error rate {obs.error_rate:.2f}% materially exceeds baseline "
                        f"{base_err_rate:.2f}% (spike: {obs.error_count}/{obs.request_count} requests failed)."
                    ),
                    confidence=0.98,
                    created_at=datetime.now(timezone.utc),
                )
                findings.append(f)

            # 2. Latency / Performance Regression Check
            lat_spike = obs.p95_latency_ms > (base_p95 * cls.LATENCY_INCREASE_MULTIPLIER)
            lat_absolute = obs.p95_latency_ms > cls.MAX_P95_LATENCY_MS

            if lat_spike or lat_absolute:
                f = RuntimeFinding(
                    deployment_id=deployment.id,
                    finding_type="PERFORMANCE_REGRESSION",
                    severity="HIGH" if obs.p95_latency_ms > 500.0 else "MEDIUM",
                    service_name=obs.service_name,
                    endpoint_or_metric=f"{obs.endpoint} (p95_latency_ms)",
                    baseline_value=base_p95,
                    observed_value=obs.p95_latency_ms,
                    threshold_value=min(cls.MAX_P95_LATENCY_MS, base_p95 * cls.LATENCY_INCREASE_MULTIPLIER),
                    evidence=(
                        f"Observed p95 latency {obs.p95_latency_ms:.1f}ms exceeds baseline {base_p95:.1f}ms."
                    ),
                    confidence=0.95,
                    created_at=datetime.now(timezone.utc),
                )
                findings.append(f)

            # 3. 5xx Server Error / Availability Check
            if obs.request_count > 0:
                rate_5xx = (obs.status_5xx_count / obs.request_count) * 100.0
                if rate_5xx > cls.MAX_ALLOWED_5XX_PERCENT:
                    f = RuntimeFinding(
                        deployment_id=deployment.id,
                        finding_type="AVAILABILITY_REGRESSION",
                        severity="CRITICAL" if rate_5xx > 3.0 else "HIGH",
                        service_name=obs.service_name,
                        endpoint_or_metric=f"{obs.endpoint} (5xx_rate)",
                        baseline_value=0.0,
                        observed_value=round(rate_5xx, 2),
                        threshold_value=cls.MAX_ALLOWED_5XX_PERCENT,
                        evidence=f"Endpoint returning {obs.status_5xx_count} 5xx server errors ({rate_5xx:.2f}% of total traffic).",
                        confidence=0.99,
                        created_at=datetime.now(timezone.utc),
                    )
                    findings.append(f)

            # 4. Healthy confirmation if no regressions for this service
            has_regressions_for_svc = any(f.service_name == obs.service_name for f in findings)
            if not has_regressions_for_svc and obs.request_count > 0:
                f = RuntimeFinding(
                    deployment_id=deployment.id,
                    finding_type="RUNTIME_HEALTHY",
                    severity="LOW",
                    service_name=obs.service_name,
                    endpoint_or_metric=obs.endpoint,
                    baseline_value=base_err_rate,
                    observed_value=obs.error_rate,
                    threshold_value=cls.MAX_ALLOWED_ERROR_RATE_PERCENT,
                    evidence=(
                        f"Observed traffic ({obs.request_count} requests, error rate {obs.error_rate:.2f}%, "
                        f"p95 {obs.p95_latency_ms:.1f}ms) operates strictly within healthy baseline parameters."
                    ),
                    confidence=0.95,
                    created_at=datetime.now(timezone.utc),
                )
                findings.append(f)

        for f in findings:
            db.add(f)
        db.commit()

        for f in findings:
            db.refresh(f)

        return findings

    @classmethod
    def determine_runtime_decision(cls, findings: List[RuntimeFinding]) -> str:
        """
        Derive the aggregate runtime decision based on findings.
        Returns: RUNTIME_VERIFIED, RUNTIME_WARNING, RUNTIME_REGRESSION, INSUFFICIENT_RUNTIME_EVIDENCE
        """
        if any(f.finding_type == "INSUFFICIENT_RUNTIME_EVIDENCE" for f in findings):
            return "INSUFFICIENT_RUNTIME_EVIDENCE"

        if any(f.severity == "CRITICAL" for f in findings) or any("REGRESSION" in f.finding_type for f in findings if f.severity in ["CRITICAL", "HIGH"]):
            return "RUNTIME_REGRESSION"

        if any(f.severity in ["MEDIUM", "HIGH"] for f in findings):
            return "RUNTIME_WARNING"

        return "RUNTIME_VERIFIED"

    @classmethod
    def build_extended_change_proof(
        cls,
        db: Session,
        change_id: str,
        deployment_id: Optional[str] = None,
    ) -> ExtendedChangeProofResponse:
        """
        Builds the Phase 4 Extended Change Proof linking pre-deployment assurance
        with post-deployment runtime telemetry and verification findings.
        """
        # 1. Fetch Phase 3 Change Proof
        phase3_proof = db.query(ChangeProof).filter(ChangeProof.change_id == change_id).order_by(ChangeProof.created_at.desc()).first()
        phase3_decision = phase3_proof.decision if phase3_proof else "UNKNOWN"
        phase3_risk = phase3_proof.risk_level if phase3_proof else "LOW"
        analysis_run_id = phase3_proof.analysis_run_id if phase3_proof else "unknown"

        # 2. Fetch or select deployment
        deployment: Optional[Deployment] = None
        if deployment_id:
            deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        else:
            deployment = db.query(Deployment).filter(Deployment.change_id == change_id).order_by(Deployment.created_at.desc()).first()

        deployment_evidence: Optional[Dict[str, Any]] = None
        runtime_evidence: Optional[Dict[str, Any]] = None
        pred_vs_obs_report: Optional[PredictionVsObservedReport] = None
        findings_resp: List[RuntimeFindingResponse] = []
        runtime_decision = "INSUFFICIENT_RUNTIME_EVIDENCE"

        if deployment:
            deployment_evidence = {
                "deployment_id": deployment.id,
                "commit_sha": deployment.commit_sha,
                "environment": deployment.environment,
                "status": deployment.status,
                "deployed_at": deployment.deployed_at.isoformat(),
            }

            # Evaluate or retrieve findings
            findings = db.query(RuntimeFinding).filter(RuntimeFinding.deployment_id == deployment.id).all()
            if not findings:
                findings = cls.evaluate_runtime_assurance(db, deployment)

            runtime_decision = cls.determine_runtime_decision(findings)

            observations = db.query(RuntimeObservation).filter(RuntimeObservation.deployment_id == deployment.id).all()
            total_req = sum(o.request_count for o in observations)
            total_err = sum(o.error_count for o in observations)
            overall_err_rate = (total_err / total_req * 100.0) if total_req > 0 else 0.0
            avg_p95 = sum(o.p95_latency_ms for o in observations) / len(observations) if observations else 0.0

            runtime_evidence = {
                "observed_services_count": len(set(o.service_name for o in observations)),
                "total_requests_observed": total_req,
                "total_errors_observed": total_err,
                "aggregate_error_rate_pct": round(overall_err_rate, 2),
                "avg_p95_latency_ms": round(avg_p95, 2),
                "regressions_detected": [f.finding_type for f in findings if "REGRESSION" in f.finding_type],
            }

            pred_vs_obs_report = PredictionMatcher.compare_prediction_vs_observed(db, deployment)

            findings_resp = [
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
            ]

        # 3. Final Combined Verdict
        if phase3_decision == "BLOCK":
            final_verdict = "BLOCKED_PRE_DEPLOYMENT"
        elif runtime_decision == "RUNTIME_REGRESSION":
            final_verdict = "RUNTIME_REGRESSION_DETECTED"
        elif runtime_decision == "RUNTIME_WARNING":
            final_verdict = "DEPLOYED_WITH_RUNTIME_WARNINGS"
        elif runtime_decision == "RUNTIME_VERIFIED":
            final_verdict = "VERIFIED_SAFE_IN_RUNTIME"
        else:
            final_verdict = "INSUFFICIENT_RUNTIME_EVIDENCE"

        auditable_record = {
            "proof_version": "2.0.0-phase4",
            "change_id": change_id,
            "analysis_run_id": analysis_run_id,
            "pre_deployment_assurance": {
                "decision": phase3_decision,
                "risk_level": phase3_risk,
            },
            "post_deployment_assurance": {
                "runtime_decision": runtime_decision,
                "final_verdict": final_verdict,
            },
            "deployment": deployment_evidence,
            "runtime_telemetry": runtime_evidence,
            "prediction_vs_observation": pred_vs_obs_report.model_dump() if pred_vs_obs_report else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return ExtendedChangeProofResponse(
            change_id=change_id,
            analysis_run_id=analysis_run_id,
            deployment_id=deployment.id if deployment else None,
            phase3_decision=phase3_decision,
            runtime_decision=runtime_decision,
            risk_level=phase3_risk,
            deployment_evidence=deployment_evidence,
            runtime_evidence=runtime_evidence,
            prediction_vs_observed=pred_vs_obs_report,
            runtime_findings=findings_resp,
            final_combined_verdict=final_verdict,
            auditable_record=auditable_record,
            created_at=datetime.now(timezone.utc),
        )
