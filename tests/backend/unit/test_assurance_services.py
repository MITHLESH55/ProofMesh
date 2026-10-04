import pytest
from app.services.assurance.intent_analyzer import IntentAnalyzer
from app.services.assurance.invariant_engine import InvariantEngine
from app.services.assurance.contract_analyzer import ContractAnalyzer
from app.services.assurance.security_analyzer import SecurityAnalyzer
from app.services.assurance.test_recommender import TestRecommender
from app.services.assurance.risk_engine import RiskEngine
from app.services.assurance.policy_engine import PolicyEngine
from app.services.assurance.change_proof_builder import ChangeProofBuilder


def test_intent_analyzer():
    analyzer = IntentAnalyzer()
    intent = analyzer.analyze_intent(
        title="Fix authentication token expiration",
        description="Handles expired JWTs cleanly",
        commit_sha="abc12345678",
        changed_files=["app/api/v1/auth.py"],
        diff_text="diff --git a/app/api/v1/auth.py\n+ # Token check\n",
    )
    assert intent["category"] in ["BUG_FIX", "SECURITY"]
    assert intent["confidence"] >= 0.8
    assert "app/api/v1/auth.py" in intent["affected_components"]
    assert "model_info" in intent


def test_invariant_engine_deterministic_auth_violation():
    engine = InvariantEngine()
    diff = """
    def authorize(user, org_id):
-       if not user.has_org(org_id):
-           return False
+       return True
    """
    invariants = engine.evaluate_invariants(
        changed_files=["app/services/auth/service.py"],
        diff_text=diff,
    )
    assert len(invariants) >= 1
    det_inv = next(i for i in invariants if i["invariant_type"] == "DETERMINISTIC")
    assert det_inv["verification_status"] == "VIOLATED"
    assert "Unauthorized actors" in det_inv["description"]


def test_contract_analyzer_breaking_change():
    analyzer = ContractAnalyzer()
    diff = """
- @router.delete("/users/{user_id}")
- def delete_user(user_id: str):
-     pass
    """
    contracts = analyzer.analyze_contracts(
        changed_files=["app/api/v1/users.py"],
        diff_text=diff,
    )
    assert len(contracts) >= 1
    breaking = [c for c in contracts if c["classification"] == "BREAKING"]
    assert len(breaking) == 1
    assert breaking[0]["endpoint_path"] == "/users/{user_id}"
    assert breaking[0]["http_method"] == "DELETE"


def test_contract_analyzer_additive_change():
    analyzer = ContractAnalyzer()
    diff = """
+ @router.get("/metrics")
+ def get_metrics():
+     return {"ok": True}
    """
    contracts = analyzer.analyze_contracts(
        changed_files=["app/api/v1/metrics.py"],
        diff_text=diff,
    )
    assert len(contracts) >= 1
    comp = [c for c in contracts if c["classification"] == "COMPATIBLE_CHANGE"]
    assert len(comp) == 1
    assert comp[0]["endpoint_path"] == "/metrics"


def test_security_analyzer_authorization_bypass():
    analyzer = SecurityAnalyzer()
    diff = """
    def is_authorized(user_role):
-       return user_role == "ADMIN"
+       return True
    """
    findings = analyzer.analyze_security(
        changed_files=["app/services/auth.py"],
        diff_text=diff,
    )
    assert len(findings) >= 1
    bypass = next(f for f in findings if f["category"] == "AUTHORIZATION_BYPASS")
    assert bypass["severity"] == "CRITICAL"
    assert bypass["confidence"] >= 0.9


def test_test_recommender():
    recommender = TestRecommender()
    recs = recommender.generate_recommendations(
        changed_files=["app/services/auth.py"],
        title="Refactor auth token refresh",
        invariants=[{
            "description": "Unauthorized access rejected",
            "affected_component": "app/services/auth.py",
            "invariant_type": "DETERMINISTIC",
        }],
        contracts=[{
            "endpoint_path": "/api/v1/auth/token",
            "http_method": "POST",
            "classification": "COMPATIBLE_CHANGE",
        }],
    )
    assert len(recs) >= 2
    titles = [r["test_title"] for r in recs]
    assert any("invariant" in t for t in titles)
    assert any("contract" in t for t in titles)


def test_risk_engine_explainable_factors():
    risk = RiskEngine.calculate_risk(
        changed_files=["app/api/v1/auth.py", "app/models/entities.py"],
        blast_radius=6,
        security_findings=[{"category": "AUTHORIZATION_BYPASS", "severity": "CRITICAL", "affected_component": "auth.py"}],
        contracts=[{"endpoint_path": "/api/v1/auth", "classification": "BREAKING"}],
        invariants=[{"verification_status": "VIOLATED", "description": "Auth check required"}],
        has_tests_modified=False,
    )
    assert risk["overall_risk"] == "CRITICAL"
    assert risk["numerical_score"] >= 70.0
    factor_names = [f["name"] for f in risk["contributing_factors"]]
    assert "CRITICAL_COMPONENT_AUTHENTICATION" in factor_names
    assert "CRITICAL_SECURITY_FINDINGS" in factor_names
    assert "BREAKING_API_CONTRACT" in factor_names
    assert "INVARIANT_VIOLATION" in factor_names
    assert len(risk["uncertainties"]) >= 1


def test_policy_engine_blocking_and_insufficient_evidence():
    # 1. Insufficient Evidence
    decision_insufficient = PolicyEngine.evaluate(
        risk_assessment={"overall_risk": "LOW", "numerical_score": 10.0},
        security_findings=[],
        contracts=[],
        invariants=[],
        evidence_count=0,
    )
    assert decision_insufficient["decision"] == "INSUFFICIENT_EVIDENCE"

    # 2. Critical Security Block
    decision_block = PolicyEngine.evaluate(
        risk_assessment={"overall_risk": "HIGH", "numerical_score": 60.0},
        security_findings=[{"category": "AUTHORIZATION_BYPASS", "severity": "CRITICAL", "reasoning": "Permissive bypass"}],
        contracts=[],
        invariants=[],
        evidence_count=5,
    )
    assert decision_block["decision"] == "BLOCK"
    assert len(decision_block["blocking_reasons"]) >= 1

    # 3. Clean Pass
    decision_pass = PolicyEngine.evaluate(
        risk_assessment={"overall_risk": "LOW", "numerical_score": 15.0},
        security_findings=[],
        contracts=[],
        invariants=[{"verification_status": "VERIFIED"}],
        evidence_count=3,
    )
    assert decision_pass["decision"] == "PASS"


def test_change_proof_builder():
    proof = ChangeProofBuilder.build_proof(
        change_id="change-001",
        commit_sha="deadbeef1234",
        analysis_run_id="run-001",
        intent={"objective": "Update auth logic", "category": "SECURITY", "affected_components": ["auth.py"]},
        impact_summary={"total_files_affected": 2, "directly_impacted": ["auth.py"], "transitively_impacted": []},
        invariants=[{"description": "Reject unauthenticated actors", "verification_status": "VERIFIED"}],
        contracts=[],
        security_findings=[],
        test_recommendations=[{"test_title": "test_auth_integrity"}],
        risk_assessment={"overall_risk": "LOW", "numerical_score": 20.0, "contributing_factors": []},
        evidence_records=[{"source_type": "CODE_DIFF", "source_reference": "auth.py"}],
        policy_decision={"decision": "PASS", "blocking_reasons": [], "warning_reasons": [], "rules_evaluated": []},
    )
    assert proof["decision"] == "PASS"
    assert proof["risk_level"] == "LOW"
    assert "summary" in proof
    assert "full_proof_artifact" in proof
    assert proof["summary"]["commit_sha"] == "deadbeef1234"
    assert "1_change_summary" in proof["full_proof_artifact"]
    assert "10_policy_decision" in proof["full_proof_artifact"]
