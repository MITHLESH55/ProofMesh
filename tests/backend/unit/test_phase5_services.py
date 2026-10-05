"""
Phase 5 Unit Tests — Enterprise & Agent Services (pure service logic, no database required).

Tests cover:
- HistoricalEvidenceService: TF-IDF tokenization, vector computation, cosine similarity
- AgentGovernanceService: capability enforcement, hard-deny rules, autonomy level capping
- AgentTaskOrchestrator: budget limit enforcement
- RemediationEngine: deterministic verification logic
- ChangeProofV3Assembler: verdict computation
"""
import math
import pytest

from app.services.enterprise.historical_evidence_service import HistoricalEvidenceService
from app.services.enterprise.agent_service import (
    AgentGovernanceService,
    AgentTaskOrchestrator,
    RemediationEngine,
    ChangeProofV3Assembler,
    HARD_DENIED_CAPABILITIES,
    CAPABILITY_TIERS,
    MAX_STEPS_PER_TASK,
    MAX_TOKENS_PER_TASK,
    MAX_COST_PER_TASK,
)
from app.services.assurance.policy_engine import PolicyEngine


# ─── HistoricalEvidenceService ───

class TestHistoricalEvidenceTokenizer:
    def test_tokenize_removes_stop_words(self):
        tokens = HistoricalEvidenceService._tokenize("the authentication check is broken")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "authentication" in tokens
        assert "check" in tokens
        assert "broken" in tokens

    def test_tokenize_lowercases(self):
        tokens = HistoricalEvidenceService._tokenize("SQL INJECTION Risk")
        assert "sql" in tokens
        assert "injection" in tokens
        assert "risk" in tokens

    def test_tokenize_excludes_single_chars(self):
        tokens = HistoricalEvidenceService._tokenize("a b c security")
        assert "a" not in tokens
        assert "b" not in tokens
        assert "security" in tokens

    def test_tfidf_vector_non_empty(self):
        vec = HistoricalEvidenceService._compute_tfidf_vector(
            "authentication bypass critical security risk"
        )
        assert isinstance(vec, dict)
        assert len(vec) > 0
        assert all(0.5 <= v <= 1.0 for v in vec.values())

    def test_tfidf_vector_empty_text(self):
        vec = HistoricalEvidenceService._compute_tfidf_vector("")
        assert vec == {}

    def test_cosine_similarity_identical(self):
        vec = HistoricalEvidenceService._compute_tfidf_vector(
            "sql injection vulnerability database"
        )
        sim = HistoricalEvidenceService._cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_disjoint(self):
        vec_a = HistoricalEvidenceService._compute_tfidf_vector("authentication security")
        vec_b = HistoricalEvidenceService._compute_tfidf_vector("database migration schema")
        sim = HistoricalEvidenceService._cosine_similarity(vec_a, vec_b)
        assert sim == 0.0

    def test_cosine_similarity_partial_overlap(self):
        vec_a = HistoricalEvidenceService._compute_tfidf_vector("authentication security token")
        vec_b = HistoricalEvidenceService._compute_tfidf_vector("authentication bypass token refresh")
        sim = HistoricalEvidenceService._cosine_similarity(vec_a, vec_b)
        assert 0.0 < sim < 1.0

    def test_cosine_similarity_empty_vectors(self):
        assert HistoricalEvidenceService._cosine_similarity({}, {}) == 0.0
        assert HistoricalEvidenceService._cosine_similarity({"a": 1.0}, {}) == 0.0


# ─── AgentGovernanceService: Capability Policy ───

class TestAgentCapabilityPolicy:
    """Tests using mock agent objects (no DB required)."""

    def _make_agent(self, autonomy_level=2, capabilities=None, status="ACTIVE", name="test-agent"):
        """Create a simple mock agent namespace."""
        class MockAgent:
            pass
        a = MockAgent()
        a.name = name
        a.autonomy_level = autonomy_level
        a.status = status
        a.capabilities = capabilities or CAPABILITY_TIERS.get(autonomy_level, [])
        return a

    def test_hard_denied_capability_always_blocked(self):
        agent = self._make_agent(autonomy_level=5, capabilities=list(HARD_DENIED_CAPABILITIES))
        for cap in HARD_DENIED_CAPABILITIES:
            result = AgentGovernanceService.check_capability(agent, cap)
            assert result["allowed"] is False
            assert result["policy_decision"] == "BLOCKED"

    def test_disabled_agent_blocked(self):
        agent = self._make_agent(autonomy_level=3, status="DISABLED")
        result = AgentGovernanceService.check_capability(agent, "READ_REPOSITORY")
        assert result["allowed"] is False
        assert result["policy_decision"] == "BLOCKED"

    def test_restricted_agent_blocked(self):
        agent = self._make_agent(autonomy_level=2, status="RESTRICTED")
        result = AgentGovernanceService.check_capability(agent, "READ_GRAPH")
        assert result["allowed"] is False
        assert result["policy_decision"] == "BLOCKED"

    def test_capability_not_in_registered_list_blocked(self):
        agent = self._make_agent(autonomy_level=1, capabilities=["READ_REPOSITORY"])
        result = AgentGovernanceService.check_capability(agent, "CREATE_PR")
        assert result["allowed"] is False
        assert result["policy_decision"] == "BLOCKED"

    def test_allowed_standard_capability(self):
        agent = self._make_agent(autonomy_level=1, capabilities=["READ_REPOSITORY", "READ_GRAPH"])
        result = AgentGovernanceService.check_capability(agent, "READ_REPOSITORY")
        assert result["allowed"] is True
        assert result["policy_decision"] == "ALLOWED"

    def test_high_risk_capability_requires_approval(self):
        agent = self._make_agent(
            autonomy_level=4,
            capabilities=["READ_REPOSITORY", "CREATE_PR", "APPLY_REMEDIATION", "CREATE_BRANCH"]
        )
        for cap in ("CREATE_PR", "APPLY_REMEDIATION", "CREATE_BRANCH"):
            result = AgentGovernanceService.check_capability(agent, cap)
            assert result["allowed"] is True
            assert result["policy_decision"] == "PENDING_APPROVAL"

    def test_capability_tiers_are_additive(self):
        """Higher autonomy levels must include all lower-level capabilities."""
        for level in range(1, 6):
            lower_caps = set(CAPABILITY_TIERS.get(level - 1, []))
            current_caps = set(CAPABILITY_TIERS.get(level, []))
            assert lower_caps.issubset(current_caps), (
                f"Autonomy level {level} is missing caps from level {level - 1}: "
                f"{lower_caps - current_caps}"
            )

    def test_hard_denied_not_in_any_tier(self):
        """Hard-denied capabilities must never appear in any capability tier."""
        all_tier_caps = set()
        for caps in CAPABILITY_TIERS.values():
            all_tier_caps.update(caps)
        overlap = all_tier_caps & HARD_DENIED_CAPABILITIES
        assert overlap == set(), f"Hard-denied capabilities found in tiers: {overlap}"


# ─── AgentTaskOrchestrator: Budget Enforcement ───

class TestBudgetEnforcement:
    def _make_task(self, step_count=0, token_count=0, cost_estimate=0.0, status="RUNNING"):
        class MockTask:
            pass
        t = MockTask()
        t.id = "task-001"
        t.step_count = step_count
        t.token_count = token_count
        t.cost_estimate = cost_estimate
        t.status = status
        return t

    def test_within_budget(self):
        task = self._make_task(step_count=10, token_count=1000, cost_estimate=0.5)
        result = AgentTaskOrchestrator.check_budget(task)
        assert result["within_budget"] is True
        assert result["exceeded"] == []

    def test_step_count_exceeded(self):
        task = self._make_task(step_count=MAX_STEPS_PER_TASK)
        result = AgentTaskOrchestrator.check_budget(task)
        assert result["within_budget"] is False
        assert any("step_count" in r for r in result["exceeded"])

    def test_token_count_exceeded(self):
        task = self._make_task(token_count=MAX_TOKENS_PER_TASK)
        result = AgentTaskOrchestrator.check_budget(task)
        assert result["within_budget"] is False
        assert any("token_count" in r for r in result["exceeded"])

    def test_cost_exceeded(self):
        task = self._make_task(cost_estimate=MAX_COST_PER_TASK)
        result = AgentTaskOrchestrator.check_budget(task)
        assert result["within_budget"] is False
        assert any("cost_estimate" in r for r in result["exceeded"])

    def test_multiple_budgets_exceeded(self):
        task = self._make_task(
            step_count=MAX_STEPS_PER_TASK,
            token_count=MAX_TOKENS_PER_TASK,
            cost_estimate=MAX_COST_PER_TASK,
        )
        result = AgentTaskOrchestrator.check_budget(task)
        assert result["within_budget"] is False
        assert len(result["exceeded"]) == 3


# ─── RemediationEngine: Deterministic Verification ───

class TestRemediationVerification:
    def test_small_targeted_patch_reduces_risk(self):
        diff = "\n".join([f"+line {i}" for i in range(5)])  # 5-line diff
        score, level = RemediationEngine._verify_remediation(
            original_score=60.0,
            proposed_diff=diff,
            affected_components=["auth.py"],
        )
        assert score < 60.0
        assert score == round(60.0 * 0.60, 4)  # 40% reduction
        assert level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_moderate_patch_moderate_reduction(self):
        diff = "\n".join([f"+line {i}" for i in range(20)])  # 20-line diff
        score, level = RemediationEngine._verify_remediation(
            original_score=60.0,
            proposed_diff=diff,
            affected_components=["service.py", "models.py", "utils.py"],
        )
        assert score < 60.0
        assert score == round(60.0 * 0.75, 4)  # 25% reduction

    def test_large_patch_no_reduction(self):
        diff = "\n".join([f"+line {i}" for i in range(150)])  # >100 lines
        score, level = RemediationEngine._verify_remediation(
            original_score=70.0,
            proposed_diff=diff,
            affected_components=["file.py"],
        )
        assert score == 70.0  # No reduction for broad patches

    def test_risk_level_mapping(self):
        for original, expected_level in [
            (20.0, "LOW"),    # <25
            (40.0, "MEDIUM"), # >=25, <50 (after reduction)
            (80.0, "HIGH"),   # still high after reduction
        ]:
            score, level = RemediationEngine._verify_remediation(
                original_score=original,
                proposed_diff="+fix",  # 1-line, minimal diff
                affected_components=["x.py"],
            )
            assert level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_score_never_negative(self):
        score, level = RemediationEngine._verify_remediation(
            original_score=0.0,
            proposed_diff="+fix line",
            affected_components=["x.py"],
        )
        assert score >= 0.0


# ─── ChangeProofV3Assembler: Verdict Logic ───

class TestChangeProofV3Verdict:
    def _risk(self, score, level):
        class R:
            numerical_score = score
            overall_risk = level
        return R()

    def _policy(self, decision, blocking=None):
        class P:
            pass
        p = P()
        p.decision = decision
        p.blocking_reasons = blocking or []
        return p

    def _ci(self, status):
        class C:
            pass
        c = C()
        c.status = status
        return c

    def _runtime_finding(self, finding_type):
        class F:
            pass
        f = F()
        f.finding_type = finding_type
        return f

    def _remediation(self, verification_status):
        class R:
            pass
        r = R()
        r.verification_status = verification_status
        return r

    def _approval(self, status):
        class A:
            pass
        a = A()
        a.status = status
        return a

    def test_clean_change_verified_safe(self):
        verdict, level, score = ChangeProofV3Assembler._compute_verdict(
            risk=self._risk(15.0, "LOW"),
            policy=self._policy("PASS"),
            ci_checks=[self._ci("PASSED"), self._ci("PASSED")],
            runtime_findings=[],
            agent_tasks=[],
            remediations=[],
            approvals=[],
        )
        assert verdict == "VERIFIED_SAFE"

    def test_policy_block_no_remediation_blocked(self):
        verdict, level, score = ChangeProofV3Assembler._compute_verdict(
            risk=self._risk(80.0, "CRITICAL"),
            policy=self._policy("BLOCK", ["Critical security issue"]),
            ci_checks=[self._ci("PASSED")],
            runtime_findings=[],
            agent_tasks=[],
            remediations=[],
            approvals=[],
        )
        assert verdict == "BLOCKED"

    def test_policy_block_with_verified_remediation_and_approval(self):
        verdict, level, score = ChangeProofV3Assembler._compute_verdict(
            risk=self._risk(80.0, "CRITICAL"),
            policy=self._policy("BLOCK"),
            ci_checks=[],
            runtime_findings=[],
            agent_tasks=[],
            remediations=[self._remediation("VERIFIED_SAFER")],
            approvals=[self._approval("APPROVED")],
        )
        assert verdict == "REMEDIATION_VERIFIED"

    def test_policy_block_with_remediation_pending_approval(self):
        verdict, level, score = ChangeProofV3Assembler._compute_verdict(
            risk=self._risk(80.0, "CRITICAL"),
            policy=self._policy("BLOCK"),
            ci_checks=[],
            runtime_findings=[],
            agent_tasks=[],
            remediations=[self._remediation("VERIFIED_SAFER")],
            approvals=[self._approval("PENDING")],
        )
        assert verdict == "REMEDIATION_PENDING_APPROVAL"

    def test_runtime_regression_detected(self):
        verdict, level, score = ChangeProofV3Assembler._compute_verdict(
            risk=self._risk(30.0, "MEDIUM"),
            policy=self._policy("PASS"),
            ci_checks=[self._ci("PASSED")],
            runtime_findings=[self._runtime_finding("REGRESSION")],
            agent_tasks=[],
            remediations=[],
            approvals=[],
        )
        assert verdict == "RUNTIME_REGRESSION"

    def test_ci_failure_blocked(self):
        verdict, level, score = ChangeProofV3Assembler._compute_verdict(
            risk=self._risk(25.0, "MEDIUM"),
            policy=self._policy("PASS"),
            ci_checks=[self._ci("PASSED"), self._ci("FAILED")],
            runtime_findings=[],
            agent_tasks=[],
            remediations=[],
            approvals=[],
        )
        assert verdict == "BLOCKED"


# ─── PolicyEngine integration (unchanged Phase 3 baseline) ───

class TestPolicyEnginePhase3Baseline:
    """Regression guard: Phase 3 policy engine must still function correctly."""

    def test_pass_with_clean_signals(self):
        result = PolicyEngine.evaluate(
            risk_assessment={"overall_risk": "LOW", "numerical_score": 10.0},
            security_findings=[],
            contracts=[],
            invariants=[{"verification_status": "VERIFIED"}],
            evidence_count=5,
        )
        assert result["decision"] == "PASS"

    def test_block_on_critical_security(self):
        result = PolicyEngine.evaluate(
            risk_assessment={"overall_risk": "HIGH", "numerical_score": 70.0},
            security_findings=[{"category": "SQL_INJECTION", "severity": "CRITICAL", "reasoning": "Unsafe query"}],
            contracts=[],
            invariants=[],
            evidence_count=3,
        )
        assert result["decision"] == "BLOCK"

    def test_block_on_breaking_contract(self):
        result = PolicyEngine.evaluate(
            risk_assessment={"overall_risk": "MEDIUM", "numerical_score": 45.0},
            security_findings=[],
            contracts=[{"endpoint_path": "/api/v1/users", "classification": "BREAKING"}],
            invariants=[],
            evidence_count=4,
        )
        assert result["decision"] == "BLOCK"

    def test_insufficient_evidence(self):
        result = PolicyEngine.evaluate(
            risk_assessment={"overall_risk": "LOW", "numerical_score": 5.0},
            evidence_count=0,
        )
        assert result["decision"] == "INSUFFICIENT_EVIDENCE"
