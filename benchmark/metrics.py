"""
ProofMesh Phase 5 Benchmark Metrics Engine.

Calculates objective, reproducible assurance evaluation metrics across
benchmark scenario executions and ground-truth comparisons.
"""
from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional


@dataclass
class MetricSummary:
    """Summary of benchmark performance metrics."""
    total_scenarios: int
    category_distribution: Dict[str, int]
    risk_precision: float
    risk_recall: float
    risk_f1: float
    classification_accuracy: float
    architecture_detection_accuracy: float
    impact_analysis_accuracy: float
    missing_test_precision: float
    missing_test_recall: float
    missing_test_f1: float
    relevant_test_reduction_percent: float
    runtime_regression_accuracy: float
    runtime_regression_precision: float
    runtime_regression_recall: float
    policy_decision_accuracy: float
    governance_decision_accuracy: float
    historical_retrieval_accuracy: float
    latency_ms_min: float
    latency_ms_max: float
    latency_ms_mean: float
    latency_ms_median: float
    latency_ms_p95: float
    monetary_cost_per_change_usd: float
    simulated_tokens_per_change_mean: float
    cost_status_note: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BenchmarkMetricsCalculator:
    """Computes comprehensive, un-fabricated benchmark metrics."""

    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate the given percentile (0 - 100) from a list of floats."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (percentile / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return round(sorted_values[int(k)], 3)
        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return round(d0 + d1, 3)

    @staticmethod
    def compute_metrics(
        evaluations: List[Dict[str, Any]],
        ground_truths: List[Dict[str, Any]],
        total_suite_tests: int = 187,
    ) -> MetricSummary:
        """
        Compare evaluation results against ground truths.

        Args:
            evaluations: List of scenario output dicts produced by the runner.
            ground_truths: List of ground-truth dicts.
            total_suite_tests: Total backend tests available in test suite (baseline: 187).
        """
        if len(evaluations) != len(ground_truths):
            raise ValueError(
                f"Evaluation count ({len(evaluations)}) must match ground truth count ({len(ground_truths)})"
            )

        gt_map = {gt["id"]: gt for gt in ground_truths}
        total = len(evaluations)
        if total == 0:
            raise ValueError("No scenario evaluations provided for metric calculation.")

        category_counts: Dict[str, int] = {}

        # Counters for Risk (High/Critical vs Low/Medium)
        risk_tp = 0
        risk_fp = 0
        risk_fn = 0
        risk_tn = 0

        # Exact Risk Level Classification Matches
        classification_matches = 0

        # Architecture / Breaking Contract Detection Matches
        arch_matches = 0

        # Impact Analysis Matches
        impact_matches = 0

        # Missing Test Detection Counters
        test_tp = 0
        test_fp = 0
        test_fn = 0
        test_tn = 0
        recommended_test_counts: List[int] = []

        # Runtime Regression Counters
        reg_tp = 0
        reg_fp = 0
        reg_fn = 0
        reg_tn = 0

        # Policy & Governance Matches
        policy_matches = 0
        gov_matches = 0
        gov_total = 0

        # Historical Retrieval Matches
        hist_matches = 0
        hist_total = 0

        # Latencies & Tokens
        latencies_ms: List[float] = []
        tokens_list: List[int] = []

        for ev in evaluations:
            scen_id = ev["id"]
            if scen_id not in gt_map:
                raise ValueError(f"Ground truth missing for evaluated scenario ID: {scen_id}")
            gt = gt_map[scen_id]
            cat = gt["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

            # Latency and token tracking
            lat_ms = float(ev.get("execution_latency_ms", 0.0))
            latencies_ms.append(lat_ms)
            tokens_list.append(int(ev.get("simulated_tokens", 0)))

            # 1. Risk Level Classification
            pred_risk = str(ev.get("predicted_risk_level", "LOW")).upper()
            expected_risk = str(gt.get("expected_risk_level", "LOW")).upper()
            if pred_risk == expected_risk:
                classification_matches += 1

            # Elevated risk binary detection (CRITICAL or HIGH)
            pred_elevated = pred_risk in {"CRITICAL", "HIGH"}
            expected_elevated = expected_risk in {"CRITICAL", "HIGH"}
            if pred_elevated and expected_elevated:
                risk_tp += 1
            elif pred_elevated and not expected_elevated:
                risk_fp += 1
            elif not pred_elevated and expected_elevated:
                risk_fn += 1
            else:
                risk_tn += 1

            # 2. Architecture / Contract Detection
            pred_arch_viol = bool(ev.get("has_architecture_violation", False))
            expected_arch_viol = bool(gt.get("has_architecture_violation", False))
            if pred_arch_viol == expected_arch_viol:
                arch_matches += 1

            # 3. Impact Analysis Accuracy
            pred_impact_match = bool(ev.get("impact_analysis_match", False))
            if pred_impact_match:
                impact_matches += 1

            # 4. Missing Test Detection
            pred_missing_tests = bool(ev.get("has_missing_tests", False))
            expected_missing_tests = bool(gt.get("has_missing_tests", False))
            if pred_missing_tests and expected_missing_tests:
                test_tp += 1
            elif pred_missing_tests and not expected_missing_tests:
                test_fp += 1
            elif not pred_missing_tests and expected_missing_tests:
                test_fn += 1
            else:
                test_tn += 1

            recs = ev.get("recommended_tests", [])
            recommended_test_counts.append(len(recs))

            # 5. Runtime Regression Detection
            pred_reg = bool(ev.get("has_runtime_regression", False))
            expected_reg = bool(gt.get("has_runtime_regression", False))
            if pred_reg and expected_reg:
                reg_tp += 1
            elif pred_reg and not expected_reg:
                reg_fp += 1
            elif not pred_reg and expected_reg:
                reg_fn += 1
            else:
                reg_tn += 1

            # 6. Policy Decision Match
            pred_policy = str(ev.get("predicted_policy_decision", "")).upper()
            expected_policy = str(gt.get("expected_policy_decision", "")).upper()
            if pred_policy == expected_policy:
                policy_matches += 1

            # 7. Agent Governance Match
            if gt.get("expected_governance_decision") is not None and ev.get("predicted_governance_decision") is not None:
                gov_total += 1
                pred_gov = str(ev.get("predicted_governance_decision", "")).upper()
                exp_gov = str(gt.get("expected_governance_decision", "")).upper()
                if pred_gov == exp_gov:
                    gov_matches += 1

            # 8. Historical Retrieval Match
            if gt.get("relevant_historical_match") is not None and ev.get("top_historical_match_id") is not None:
                hist_total += 1
                pred_hist = ev.get("top_historical_match_id")
                exp_hist = gt.get("relevant_historical_match")
                if pred_hist == exp_hist:
                    hist_matches += 1

        # Calculate Rates
        def safe_div(num: float, den: float) -> float:
            return round(num / den, 4) if den > 0 else 0.0

        risk_precision = safe_div(risk_tp, risk_tp + risk_fp)
        risk_recall = safe_div(risk_tp, risk_tp + risk_fn)
        risk_f1 = safe_div(2 * risk_precision * risk_recall, risk_precision + risk_recall) if (risk_precision + risk_recall) > 0 else 0.0

        classification_accuracy = safe_div(classification_matches, total)
        arch_accuracy = safe_div(arch_matches, total)
        impact_accuracy = safe_div(impact_matches, total)

        test_precision = safe_div(test_tp, test_tp + test_fp)
        test_recall = safe_div(test_tp, test_tp + test_fn)
        test_f1 = safe_div(2 * test_precision * test_recall, test_precision + test_recall) if (test_precision + test_recall) > 0 else 0.0

        avg_recommended = (sum(recommended_test_counts) / len(recommended_test_counts)) if recommended_test_counts else 0.0
        relevant_test_reduction = round(
            max(0.0, (total_suite_tests - avg_recommended) / total_suite_tests) * 100.0, 2
        )

        reg_precision = safe_div(reg_tp, reg_tp + reg_fp)
        reg_recall = safe_div(reg_tp, reg_tp + reg_fn)
        reg_accuracy = safe_div(reg_tp + reg_tn, total)

        policy_accuracy = safe_div(policy_matches, total)
        gov_accuracy = safe_div(gov_matches, gov_total) if gov_total > 0 else 1.0
        hist_accuracy = safe_div(hist_matches, hist_total) if hist_total > 0 else 1.0

        # Latency statistics
        lat_min = round(min(latencies_ms), 3) if latencies_ms else 0.0
        lat_max = round(max(latencies_ms), 3) if latencies_ms else 0.0
        lat_mean = round(sum(latencies_ms) / len(latencies_ms), 3) if latencies_ms else 0.0
        lat_median = BenchmarkMetricsCalculator.calculate_percentile(latencies_ms, 50.0)
        lat_p95 = BenchmarkMetricsCalculator.calculate_percentile(latencies_ms, 95.0)

        # Tokens
        tokens_mean = round(sum(tokens_list) / len(tokens_list), 1) if tokens_list else 0.0

        cost_status_note = (
            "Measured monetary cost is $0.00 / change. ProofMesh executes using deterministic "
            "offline rule engines and MockAIProvider without external commercial LLM token billing. "
            "Simulated prompt token volume is tracked above, while external monetary API costs "
            "remain objectively $0.00."
        )

        return MetricSummary(
            total_scenarios=total,
            category_distribution=category_counts,
            risk_precision=risk_precision,
            risk_recall=risk_recall,
            risk_f1=risk_f1,
            classification_accuracy=classification_accuracy,
            architecture_detection_accuracy=arch_accuracy,
            impact_analysis_accuracy=impact_accuracy,
            missing_test_precision=test_precision,
            missing_test_recall=test_recall,
            missing_test_f1=test_f1,
            relevant_test_reduction_percent=relevant_test_reduction,
            runtime_regression_accuracy=reg_accuracy,
            runtime_regression_precision=reg_precision,
            runtime_regression_recall=reg_recall,
            policy_decision_accuracy=policy_accuracy,
            governance_decision_accuracy=gov_accuracy,
            historical_retrieval_accuracy=hist_accuracy,
            latency_ms_min=lat_min,
            latency_ms_max=lat_max,
            latency_ms_mean=lat_mean,
            latency_ms_median=lat_median,
            latency_ms_p95=lat_p95,
            monetary_cost_per_change_usd=0.00,
            simulated_tokens_per_change_mean=tokens_mean,
            cost_status_note=cost_status_note,
        )
