"""
Prediction vs Observed Matcher.

Correlates Phase 2 static dependency graph predictions (affected components / services)
with real post-deployment runtime telemetry traffic.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.runtime import Deployment, RuntimeObservation
from app.models.assurance import ChangeIntent
from app.schemas.runtime import ComponentTrafficStatus, PredictionVsObservedReport


class PredictionMatcher:
    """Compares static code dependency predictions with live runtime telemetry."""

    @staticmethod
    def compare_prediction_vs_observed(
        db: Session,
        deployment: Deployment,
        predicted_services: Optional[List[str]] = None,
    ) -> PredictionVsObservedReport:
        """
        Evaluate whether the services predicted to be impacted statically actually
        experienced traffic, and whether unexpected services were affected.
        """
        # If predicted_services not provided explicitly, infer from ChangeIntent or Analysis
        if predicted_services is None:
            intent = db.query(ChangeIntent).filter(ChangeIntent.change_id == deployment.change_id).first()
            if intent and intent.affected_components:
                # Extract service identifiers from affected components
                predicted_services = list(set([
                    c.split("/")[0].replace(".py", "").replace(".ts", "").replace("-service", "") + "-service"
                    if not c.endswith("-service") else c
                    for c in intent.affected_components
                ]))
            else:
                # Default fallback based on commit context or standard components
                predicted_services = ["auth-service", "user-service"]

        # Fetch actual runtime observations for this deployment
        observations = db.query(RuntimeObservation).filter(
            RuntimeObservation.deployment_id == deployment.id
        ).all()

        observed_map: Dict[str, Dict[str, Any]] = {}
        for o in observations:
            if o.service_name not in observed_map:
                observed_map[o.service_name] = {
                    "total_requests": 0,
                    "total_errors": 0,
                    "p95_latencies": [],
                }
            observed_map[o.service_name]["total_requests"] += o.request_count
            observed_map[o.service_name]["total_errors"] += o.error_count
            observed_map[o.service_name]["p95_latencies"].append(o.p95_latency_ms)

        observed_services = list(observed_map.keys())
        all_services = sorted(list(set(predicted_services + observed_services)))

        components: List[ComponentTrafficStatus] = []
        discrepancies: List[str] = []

        for svc in all_services:
            is_predicted = svc in predicted_services
            is_observed = svc in observed_map and observed_map[svc]["total_requests"] > 0
            
            sdata = observed_map.get(svc, {"total_requests": 0, "total_errors": 0, "p95_latencies": []})
            err_rate = (sdata["total_errors"] / sdata["total_requests"] * 100.0) if sdata["total_requests"] > 0 else 0.0
            avg_p95 = sum(sdata["p95_latencies"]) / len(sdata["p95_latencies"]) if sdata["p95_latencies"] else 0.0

            if is_predicted and is_observed:
                if err_rate > 5.0 or avg_p95 > 500.0:
                    status = "REGRESSION"
                    discrepancies.append(f"Predicted service '{svc}' is experiencing active regression in runtime (error rate {err_rate:.1f}%, p95 {avg_p95:.1f}ms)")
                else:
                    status = "MATCH"
            elif is_predicted and not is_observed:
                status = "UNEXPECTED_QUIET"
                discrepancies.append(f"Predicted affected service '{svc}' received 0 observed runtime requests")
            elif not is_predicted and is_observed:
                status = "UNEXPECTED_TRAFFIC"
                discrepancies.append(f"Unpredicted service '{svc}' is receiving runtime traffic under this change deployment")
            else:
                status = "MATCH"

            components.append(
                ComponentTrafficStatus(
                    service_name=svc,
                    predicted_impacted=is_predicted,
                    observed_traffic=is_observed,
                    observed_error_rate=round(err_rate, 2),
                    observed_p95_ms=round(avg_p95, 2),
                    status=status,
                )
            )

        summary_match = len([d for d in discrepancies if "regression" in d.lower()]) == 0

        return PredictionVsObservedReport(
            deployment_id=deployment.id,
            change_id=deployment.change_id,
            predicted_services=predicted_services,
            observed_services=observed_services,
            components=components,
            summary_match=summary_match,
            discrepancies=discrepancies,
        )
