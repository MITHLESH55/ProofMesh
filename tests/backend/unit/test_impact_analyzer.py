import pytest
from app.services.impact.impact_analyzer import (
    ImpactAnalyzer,
    ImpactLevel,
    ImpactedFile,
    ImpactAnalysisResult,
)


def test_impact_risk_calculation():
    # Direct should be 1.0 with no chain
    assert ImpactAnalyzer._calculate_risk(ImpactLevel.DIRECT, []) == 1.0

    # First order
    r1 = ImpactAnalyzer._calculate_risk(ImpactLevel.FIRST_ORDER, ["app/main.py"])
    assert 0.7 <= r1 <= 0.8

    # Second order
    r2 = ImpactAnalyzer._calculate_risk(ImpactLevel.SECOND_ORDER, ["app/main.py", "app/sub.py"])
    assert 0.3 <= r2 < r1

    # Transitive
    r3 = ImpactAnalyzer._calculate_risk(ImpactLevel.TRANSITIVE, ["a", "b", "c", "d"])
    assert r3 < r2


def test_compute_risk_summary_empty():
    summary = ImpactAnalyzer._compute_risk_summary(["file1.py"], [])
    assert summary["overall_risk"] == "low"
    assert summary["risk_score"] == 0.0
    assert summary["blast_radius"] == 1


def test_compute_risk_summary_high_impact():
    impacted = [
        ImpactedFile(
            path=f"file_{i}.py",
            language="python",
            impact_level=ImpactLevel.FIRST_ORDER,
            impact_chain=["main.py"],
            risk_score=0.85,
        )
        for i in range(6)
    ]
    summary = ImpactAnalyzer._compute_risk_summary(["main.py"], impacted)
    assert summary["overall_risk"] in {"high", "critical"}
    assert summary["high_risk_files"] == 6
    assert summary["blast_radius"] == 7


def test_impact_analysis_result_serialization():
    file = ImpactedFile(
        path="app/api.py",
        language="python",
        impact_level=ImpactLevel.FIRST_ORDER,
        impact_chain=["app/models.py"],
        affected_symbols=["Function:get_user"],
        risk_score=0.72,
    )
    result = ImpactAnalysisResult(
        repository_id="repo-123",
        changed_files=["app/models.py"],
        directly_impacted=[file],
        transitively_impacted=[],
        total_files_affected=2,
        risk_summary={"overall_risk": "medium", "blast_radius": 2},
    )
    d = result.to_dict()
    assert d["repository_id"] == "repo-123"
    assert len(d["directly_impacted"]) == 1
    assert d["directly_impacted"][0]["path"] == "app/api.py"
    assert d["directly_impacted"][0]["risk_score"] == 0.72
