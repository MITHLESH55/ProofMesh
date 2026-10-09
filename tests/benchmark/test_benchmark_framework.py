"""
Tests for ProofMesh Phase 5 Benchmark Framework.

Verifies:
- Scenario and ground-truth corpus integrity
- Fail-fast validation on duplicate IDs, missing fields, and counts < 100
- Metric calculation accuracy (precision, recall, p95 latency)
- Full benchmark execution and report generation
"""
import glob
import json
import os
import shutil
import tempfile
import pytest

from benchmark.metrics import BenchmarkMetricsCalculator
from benchmark.runner import BenchmarkRunner, DEFAULT_SCENARIOS_DIR, DEFAULT_GROUND_TRUTH_DIR


def test_corpus_count_at_least_100():
    """Verify that both scenarios and ground-truth directories contain at least 100 files."""
    scenarios = glob.glob(os.path.join(DEFAULT_SCENARIOS_DIR, "*.json"))
    ground_truths = glob.glob(os.path.join(DEFAULT_GROUND_TRUTH_DIR, "*.json"))

    assert len(scenarios) >= 100, f"Expected at least 100 scenarios, found {len(scenarios)}"
    assert len(ground_truths) >= 100, f"Expected at least 100 ground-truth files, found {len(ground_truths)}"
    assert len(scenarios) == len(ground_truths), "Scenario and ground-truth counts must match exactly"


def test_unique_ids_across_all_scenarios():
    """Verify all scenarios have unique IDs."""
    scenarios = glob.glob(os.path.join(DEFAULT_SCENARIOS_DIR, "*.json"))
    ids = set()
    for s_path in scenarios:
        with open(s_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        sid = data["id"]
        assert sid not in ids, f"Duplicate scenario ID found: {sid}"
        ids.add(sid)


def test_validation_fails_on_duplicate_ids():
    """Verify validation raises ValueError when duplicate scenario IDs exist."""
    with tempfile.TemporaryDirectory() as temp_scen_dir, tempfile.TemporaryDirectory() as temp_gt_dir:
        # Create duplicate scenarios
        scen1 = {"id": "DUP-001", "title": "Test 1", "category": "security_violations", "input": {}}
        scen2 = {"id": "DUP-001", "title": "Test 2", "category": "security_violations", "input": {}}

        with open(os.path.join(temp_scen_dir, "file1.json"), "w") as f:
            json.dump(scen1, f)
        with open(os.path.join(temp_scen_dir, "file2.json"), "w") as f:
            json.dump(scen2, f)

        runner = BenchmarkRunner(scenarios_dir=temp_scen_dir, ground_truth_dir=temp_gt_dir)
        with pytest.raises(ValueError, match="Duplicate scenario ID"):
            runner.load_corpus()


def test_validation_fails_on_missing_required_fields():
    """Verify validation raises ValueError when required ground-truth fields are absent."""
    with tempfile.TemporaryDirectory() as temp_scen_dir, tempfile.TemporaryDirectory() as temp_gt_dir:
        scen = {"id": "TEST-VALID", "title": "Test", "category": "security_violations", "input": {}}
        # Missing 'rationale' and 'expected_risk_level'
        gt_incomplete = {
            "id": "TEST-VALID",
            "category": "security_violations",
            "is_security_violation": True,
        }

        with open(os.path.join(temp_scen_dir, "test.json"), "w") as f:
            json.dump(scen, f)
        with open(os.path.join(temp_gt_dir, "test.json"), "w") as f:
            json.dump(gt_incomplete, f)

        runner = BenchmarkRunner(scenarios_dir=temp_scen_dir, ground_truth_dir=temp_gt_dir)
        with pytest.raises(ValueError, match="missing required field"):
            runner.load_corpus()


def test_validation_fails_when_count_less_than_100():
    """Verify validation raises ValueError if scenario count is less than 100."""
    with tempfile.TemporaryDirectory() as temp_scen_dir, tempfile.TemporaryDirectory() as temp_gt_dir:
        # Create only 5 scenarios
        for i in range(5):
            sid = f"SAMPLE-{i:03d}"
            scen = {"id": sid, "title": f"Sample {i}", "category": "safe_low_risk_changes", "input": {}}
            gt = {
                "id": sid,
                "category": "safe_low_risk_changes",
                "expected_risk_level": "LOW",
                "expected_policy_decision": "PASS",
                "is_security_violation": False,
                "has_architecture_violation": False,
                "has_missing_tests": False,
                "has_runtime_regression": False,
                "rationale": "Sample rationale",
            }
            with open(os.path.join(temp_scen_dir, f"{sid}.json"), "w") as f:
                json.dump(scen, f)
            with open(os.path.join(temp_gt_dir, f"{sid}.json"), "w") as f:
                json.dump(gt, f)

        runner = BenchmarkRunner(scenarios_dir=temp_scen_dir, ground_truth_dir=temp_gt_dir)
        with pytest.raises(ValueError, match="minimum 100 is required"):
            runner.load_corpus()


def test_percentile_calculation():
    """Verify percentile calculation correctness."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    p50 = BenchmarkMetricsCalculator.calculate_percentile(values, 50.0)
    p95 = BenchmarkMetricsCalculator.calculate_percentile(values, 95.0)

    assert p50 == 55.0
    assert 90.0 < p95 <= 100.0


def test_metrics_calculation_formulae():
    """Verify precision, recall, and accuracy computation logic."""
    evals = [
        {
            "id": "T-1",
            "predicted_risk_level": "CRITICAL",
            "has_architecture_violation": True,
            "has_missing_tests": True,
            "has_runtime_regression": False,
            "predicted_policy_decision": "BLOCK",
            "impact_analysis_match": True,
            "execution_latency_ms": 1.5,
            "simulated_tokens": 300,
            "recommended_tests": ["test_1", "test_2"],
        },
        {
            "id": "T-2",
            "predicted_risk_level": "LOW",
            "has_architecture_violation": False,
            "has_missing_tests": False,
            "has_runtime_regression": True,
            "predicted_policy_decision": "WARN",
            "impact_analysis_match": True,
            "execution_latency_ms": 2.0,
            "simulated_tokens": 400,
            "recommended_tests": [],
        },
    ]

    gts = [
        {
            "id": "T-1",
            "category": "security_violations",
            "expected_risk_level": "CRITICAL",
            "has_architecture_violation": True,
            "has_missing_tests": True,
            "has_runtime_regression": False,
            "expected_policy_decision": "BLOCK",
            "rationale": "Critical security threat",
        },
        {
            "id": "T-2",
            "category": "runtime_regressions",
            "expected_risk_level": "LOW",
            "has_architecture_violation": False,
            "has_missing_tests": False,
            "has_runtime_regression": True,
            "expected_policy_decision": "WARN",
            "rationale": "Telemetry regression",
        },
    ]

    summary = BenchmarkMetricsCalculator.compute_metrics(evals, gts, total_suite_tests=100)

    assert summary.total_scenarios == 2
    assert summary.risk_precision == 1.0
    assert summary.risk_recall == 1.0
    assert summary.classification_accuracy == 1.0
    assert summary.architecture_detection_accuracy == 1.0
    assert summary.missing_test_precision == 1.0
    assert summary.runtime_regression_accuracy == 1.0
    assert summary.latency_ms_min == 1.5
    assert summary.latency_ms_max == 2.0
    assert summary.monetary_cost_per_change_usd == 0.00


def test_full_benchmark_execution():
    """Run full benchmark runner and verify report generation."""
    with tempfile.TemporaryDirectory() as temp_results_dir:
        runner = BenchmarkRunner(results_dir=temp_results_dir)
        summary, evals = runner.run_benchmark(verbose=False)

        assert summary.total_scenarios == 110
        assert len(evals) == 110
        assert summary.risk_precision >= 0.80
        assert summary.architecture_detection_accuracy >= 0.90
        assert summary.runtime_regression_accuracy >= 0.95
        assert summary.latency_ms_p95 < 50.0  # Under 50ms SLA

        # Save and verify file creation
        json_path, md_path = runner.save_results(summary, evals)
        assert os.path.exists(json_path)
        assert os.path.exists(md_path)
        assert os.path.getsize(json_path) > 1000
        assert os.path.getsize(md_path) > 500
