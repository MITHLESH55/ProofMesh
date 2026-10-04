"""
Runtime Telemetry Service.

Ingests, stores, aggregates and queries runtime telemetry observations,
baselines, and exports Prometheus-compatible metrics.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.runtime import Deployment, RuntimeBaseline, RuntimeObservation, RuntimeFinding
from app.schemas.runtime import (
    DeploymentCreate,
    RuntimeBaselineCreate,
    RuntimeObservationCreate,
    RuntimeServiceHealthResponse,
    RuntimeMetricsSummaryResponse,
)


class TelemetryService:
    """Handles storage, retrieval, and Prometheus formatting of runtime telemetry."""

    @staticmethod
    def create_deployment(db: Session, data: DeploymentCreate) -> Deployment:
        deployment = Deployment(
            repository_id=data.repository_id,
            change_id=data.change_id,
            analysis_run_id=data.analysis_run_id,
            commit_sha=data.commit_sha,
            environment=data.environment,
            status=data.status,
            deployed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        return deployment

    @staticmethod
    def get_deployment(db: Session, deployment_id: str) -> Optional[Deployment]:
        return db.query(Deployment).filter(Deployment.id == deployment_id).first()

    @staticmethod
    def list_deployments(
        db: Session,
        repository_id: Optional[str] = None,
        change_id: Optional[str] = None,
        environment: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Deployment]:
        query = db.query(Deployment)
        if repository_id:
            query = query.filter(Deployment.repository_id == repository_id)
        if change_id:
            query = query.filter(Deployment.change_id == change_id)
        if environment:
            query = query.filter(Deployment.environment == environment)
        return query.order_by(Deployment.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def record_baseline(db: Session, data: RuntimeBaselineCreate) -> RuntimeBaseline:
        baseline = RuntimeBaseline(
            deployment_id=data.deployment_id,
            service_name=data.service_name,
            endpoint=data.endpoint,
            request_rate=data.request_rate,
            error_rate=data.error_rate,
            p50_latency_ms=data.p50_latency_ms,
            p95_latency_ms=data.p95_latency_ms,
            p99_latency_ms=data.p99_latency_ms,
            sample_window_seconds=data.sample_window_seconds,
            created_at=datetime.now(timezone.utc),
        )
        db.add(baseline)
        db.commit()
        db.refresh(baseline)
        return baseline

    @staticmethod
    def get_baselines(db: Session, deployment_id: str) -> List[RuntimeBaseline]:
        return db.query(RuntimeBaseline).filter(RuntimeBaseline.deployment_id == deployment_id).all()

    @staticmethod
    def record_observation(db: Session, data: RuntimeObservationCreate) -> RuntimeObservation:
        observation = RuntimeObservation(
            deployment_id=data.deployment_id,
            service_name=data.service_name,
            endpoint=data.endpoint,
            request_count=data.request_count,
            error_count=data.error_count,
            error_rate=data.error_rate,
            p50_latency_ms=data.p50_latency_ms,
            p95_latency_ms=data.p95_latency_ms,
            p99_latency_ms=data.p99_latency_ms,
            status_2xx_count=data.status_2xx_count,
            status_4xx_count=data.status_4xx_count,
            status_5xx_count=data.status_5xx_count,
            observed_at=datetime.now(timezone.utc),
        )
        db.add(observation)
        db.commit()
        db.refresh(observation)
        return observation

    @staticmethod
    def get_observations(db: Session, deployment_id: str) -> List[RuntimeObservation]:
        return db.query(RuntimeObservation).filter(RuntimeObservation.deployment_id == deployment_id).all()

    @staticmethod
    def get_metrics_summary(db: Session, deployment_id: Optional[str] = None) -> RuntimeMetricsSummaryResponse:
        """Calculate high-level summary of runtime health across observations."""
        query = db.query(RuntimeObservation)
        if deployment_id:
            query = query.filter(RuntimeObservation.deployment_id == deployment_id)

        obs_list = query.all()
        if not obs_list:
            return RuntimeMetricsSummaryResponse(
                deployment_id=deployment_id,
                total_requests=0,
                total_errors=0,
                overall_error_rate=0.0,
                avg_p95_latency_ms=0.0,
                services=[],
                findings_count={"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            )

        total_req = sum(o.request_count for o in obs_list)
        total_err = sum(o.error_count for o in obs_list)
        overall_err_rate = (total_err / total_req * 100.0) if total_req > 0 else 0.0
        avg_p95 = sum(o.p95_latency_ms for o in obs_list) / len(obs_list) if obs_list else 0.0

        # Group by service
        services_map: Dict[str, Dict[str, Any]] = {}
        for o in obs_list:
            if o.service_name not in services_map:
                services_map[o.service_name] = {
                    "request_count": 0,
                    "error_count": 0,
                    "p95_latencies": [],
                    "last_seen": o.observed_at,
                }
            s = services_map[o.service_name]
            s["request_count"] += o.request_count
            s["error_count"] += o.error_count
            s["p95_latencies"].append(o.p95_latency_ms)
            if o.observed_at > s["last_seen"]:
                s["last_seen"] = o.observed_at

        services_resp: List[RuntimeServiceHealthResponse] = []
        for sname, sdata in services_map.items():
            s_err_rate = (sdata["error_count"] / sdata["request_count"] * 100.0) if sdata["request_count"] > 0 else 0.0
            s_avg_p95 = sum(sdata["p95_latencies"]) / len(sdata["p95_latencies"]) if sdata["p95_latencies"] else 0.0
            
            if s_err_rate > 5.0 or s_avg_p95 > 500.0:
                status = "FAILING"
            elif s_err_rate > 1.5 or s_avg_p95 > 250.0:
                status = "DEGRADED"
            else:
                status = "HEALTHY"

            services_resp.append(
                RuntimeServiceHealthResponse(
                    service_name=sname,
                    status=status,
                    request_rate=float(sdata["request_count"]),
                    error_rate=round(s_err_rate, 2),
                    p95_latency_ms=round(s_avg_p95, 2),
                    last_seen=sdata["last_seen"],
                )
            )

        # Findings count
        findings_query = db.query(RuntimeFinding)
        if deployment_id:
            findings_query = findings_query.filter(RuntimeFinding.deployment_id == deployment_id)
        findings = findings_query.all()
        findings_count = {
            "CRITICAL": sum(1 for f in findings if f.severity == "CRITICAL"),
            "HIGH": sum(1 for f in findings if f.severity == "HIGH"),
            "MEDIUM": sum(1 for f in findings if f.severity == "MEDIUM"),
            "LOW": sum(1 for f in findings if f.severity == "LOW"),
        }

        return RuntimeMetricsSummaryResponse(
            deployment_id=deployment_id,
            total_requests=total_req,
            total_errors=total_err,
            overall_error_rate=round(overall_err_rate, 2),
            avg_p95_latency_ms=round(avg_p95, 2),
            services=services_resp,
            findings_count=findings_count,
        )

    @staticmethod
    def generate_prometheus_metrics(db: Session) -> str:
        """Format stored observations into standard Prometheus scrape text."""
        obs = db.query(RuntimeObservation).order_by(RuntimeObservation.observed_at.desc()).limit(100).all()
        
        lines = [
            "# HELP proofmesh_http_requests_total Total number of HTTP requests processed by observed services",
            "# TYPE proofmesh_http_requests_total counter",
        ]
        for o in obs:
            lines.append(
                f'proofmesh_http_requests_total{{service="{o.service_name}",endpoint="{o.endpoint}",deployment="{o.deployment_id}"}} {o.request_count}'
            )

        lines.extend([
            "# HELP proofmesh_http_errors_total Total number of HTTP error responses (4xx/5xx)",
            "# TYPE proofmesh_http_errors_total counter",
        ])
        for o in obs:
            lines.append(
                f'proofmesh_http_errors_total{{service="{o.service_name}",endpoint="{o.endpoint}",deployment="{o.deployment_id}"}} {o.error_count}'
            )

        lines.extend([
            "# HELP proofmesh_http_latency_p95_ms 95th percentile request latency in milliseconds",
            "# TYPE proofmesh_http_latency_p95_ms gauge",
        ])
        for o in obs:
            lines.append(
                f'proofmesh_http_latency_p95_ms{{service="{o.service_name}",endpoint="{o.endpoint}",deployment="{o.deployment_id}"}} {o.p95_latency_ms}'
            )

        lines.extend([
            "# HELP proofmesh_service_error_rate Percentage of requests resulting in error",
            "# TYPE proofmesh_service_error_rate gauge",
        ])
        for o in obs:
            lines.append(
                f'proofmesh_service_error_rate{{service="{o.service_name}",endpoint="{o.endpoint}",deployment="{o.deployment_id}"}} {o.error_rate}'
            )

        return "\n".join(lines) + "\n"
