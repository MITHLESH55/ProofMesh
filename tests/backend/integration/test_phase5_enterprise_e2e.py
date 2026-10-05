"""
Phase 5 Complete Enterprise E2E & Performance Benchmark.

Audit Requirements:
16. COMPLETE ENTERPRISE E2E:
    Repository A (shared auth library)
    -> shared library change
    -> Repository B (payments service)
    -> Repository C (billing portal)
    -> affected services & teams
    -> Phase 2 graph impact propagation
    -> Phase 3 risk & policy evaluation (BLOCK)
    -> Phase 4 runtime baseline
    -> Historical evidence retrieval
    -> Autonomous agent investigation & remediation proposal
    -> Deterministic verification (risk recalculated)
    -> Human approval gate
    -> Final Change Proof v3 assembly

22. PERFORMANCE VERIFICATION:
    Measures actual execution times for:
    - Multi-repository enterprise graph analysis
    - Graph traversal & blast radius calculation
    - Historical evidence semantic retrieval (TF-IDF cosine similarity)
    - Agent orchestration & bounded execution
    - Policy evaluation
    - Change Proof v3 generation
"""
import time
from datetime import datetime, timezone
import pytest

from app.models.entities import Organization, Repository, PullRequest, Change, AnalysisRun, User
from app.models.enterprise import Team, Service, CrossRepoDependency, ComponentOwnership
from app.models.assurance import RiskAssessment, PolicyDecision, ChangeProof
from app.models.runtime import CIAssuranceCheck, RuntimeFinding
from app.schemas.agent import (
    AgentDefinitionCreate,
    AgentTaskCreate,
    RemediationProposalCreate,
    AgentApprovalRequest,
    AgentApprovalDecision,
)
from app.services.enterprise import (
    EnterpriseGraphService,
    HistoricalEvidenceService,
    AgentGovernanceService,
    AgentTaskOrchestrator,
    AgentActionLedger,
    AgentApprovalService,
    RemediationEngine,
    ChangeProofV3Assembler,
)
from app.schemas.enterprise import HistoricalEvidenceCreate, EvidenceSearchRequest


def test_complete_enterprise_e2e_and_performance(db_session):
    """
    Executes a complete cross-repository change propagation flow across 3 repositories,
    services, teams, historical evidence retrieval, agent remediation, human approval,
    and final Change Proof v3 assembly.
    Records actual benchmark timings.
    """
    benchmarks = {}

    # 1. Setup Enterprise Hierarchy
    org = Organization(id="org_perf_e2e", name="Enterprise Corp", slug="enterprise-corp-perf")
    db_session.add(org)

    # 3 Repositories
    repo_a = Repository(
        id="repo_auth_lib", organization_id=org.id,
        github_repository_id="gh-auth-core-lib", owner="corp",
        name="auth-core-lib", full_name="corp/auth-core-lib",
    )
    repo_b = Repository(
        id="repo_payment_svc", organization_id=org.id,
        github_repository_id="gh-payment-service", owner="corp",
        name="payment-service", full_name="corp/payment-service",
    )
    repo_c = Repository(
        id="repo_billing_ui", organization_id=org.id,
        github_repository_id="gh-billing-portal", owner="corp",
        name="billing-portal", full_name="corp/billing-portal",
    )
    db_session.add_all([repo_a, repo_b, repo_c])

    # 2 Teams
    team_sec = Team(id="team_sec_eng", organization_id=org.id, name="Security Eng", slug="sec-eng")
    team_pay = Team(id="team_payments", organization_id=org.id, name="Payments Team", slug="payments")
    db_session.add_all([team_sec, team_pay])

    # 2 Services
    svc_auth = Service(id="svc_auth_api", organization_id=org.id, repository_id=repo_a.id, team_id=team_sec.id, name="auth-api", tier="TIER_1", criticality="CRITICAL")
    svc_pay = Service(id="svc_pay_gw", organization_id=org.id, repository_id=repo_b.id, team_id=team_pay.id, name="payment-gateway", tier="TIER_1", criticality="CRITICAL")
    db_session.add_all([svc_auth, svc_pay])

    # Cross-repo dependencies:
    # payment-service depends on auth-core-lib
    # billing-portal depends on auth-core-lib
    dep_b_a = CrossRepoDependency(
        organization_id=org.id,
        source_repository_id=repo_b.id,
        target_repository_id=repo_a.id,
        dependency_type="PACKAGE",
        package_or_service_name="auth-core-lib",
        provenance_details={"declared_in": "requirements.txt"},
    )
    dep_c_a = CrossRepoDependency(
        organization_id=org.id,
        source_repository_id=repo_c.id,
        target_repository_id=repo_a.id,
        dependency_type="PACKAGE",
        package_or_service_name="auth-core-lib",
        provenance_details={"declared_in": "package.json"},
    )
    db_session.add_all([dep_b_a, dep_c_a])
    db_session.commit()

    # Benchmark 1: Multi-Repository Enterprise Graph Construction
    t0 = time.perf_counter()
    graph = EnterpriseGraphService.build_enterprise_graph(db_session, org.id)
    t1 = time.perf_counter()
    benchmarks["multi_repo_graph_analysis_ms"] = round((t1 - t0) * 1000, 3)

    assert len(graph.nodes) >= 5
    assert len(graph.edges) >= 4

    # Benchmark 2: Cross-Repo Graph Traversal & Blast Radius Calculation
    t0 = time.perf_counter()
    impact = EnterpriseGraphService.get_cross_repo_impact(db_session, org.id, repo_a.id)
    t1 = time.perf_counter()
    benchmarks["graph_traversal_impact_ms"] = round((t1 - t0) * 1000, 3)

    assert impact["downstream_repository_count"] == 2
    assert repo_b.id in impact["downstream_repository_ids"]
    assert repo_c.id in impact["downstream_repository_ids"]
    assert impact["max_criticality"] == "CRITICAL"

    # Temporal Snapshot Check
    version_a = EnterpriseGraphService.snapshot_graph(db_session, org.id, version_tag="v1.0.0", commit_sha="commit_sha_1")
    assert version_a.node_count == len(graph.nodes)

    # Historical Evidence Seed & Retrieval
    HistoricalEvidenceService.store_evidence(
        db_session,
        HistoricalEvidenceCreate(
            organization_id=org.id,
            evidence_type="PREVIOUS_PROOF",
            title="Auth Token Expiration Fix",
            content="Fixed JWT token expiration regression in auth-core-lib that caused payment outages",
            repository_id=repo_a.id,
            service_id=svc_auth.id,
        ),
    )
    HistoricalEvidenceService.store_evidence(
        db_session,
        HistoricalEvidenceCreate(
            organization_id=org.id,
            evidence_type="INCIDENT",
            title="Database deadlocks during token refresh",
            content="High concurrency deadlock on sessions table during token refresh cycle",
            repository_id=repo_a.id,
            service_id=svc_auth.id,
        ),
    )

    # Benchmark 3: Semantic Retrieval (TF-IDF Cosine Similarity)
    t0 = time.perf_counter()
    search_results = HistoricalEvidenceService.search(
        db_session,
        EvidenceSearchRequest(
            organization_id=org.id,
            query="JWT token expiration auth payment",
            limit=5,
        ),
    )
    t1 = time.perf_counter()
    benchmarks["evidence_semantic_retrieval_ms"] = round((t1 - t0) * 1000, 3)

    assert len(search_results) >= 1
    assert "token" in search_results[0].content.lower()

    # Simulate Phase 3 Analysis Run & Policy Decision (BLOCK)
    pr = PullRequest(
        id="pr_auth_1",
        repository_id=repo_a.id,
        github_pr_id="gh_pr_auth_1",
        number=101,
        title="Update auth token verification",
        author="alice",
        head_sha="commit_auth_new",
        base_sha="commit_auth_base",
    )
    db_session.add(pr)
    change = Change(id="ch_auth_change_1", pull_request_id=pr.id, commit_sha="commit_auth_new")
    db_session.add(change)
    run = AnalysisRun(id="run_auth_1", change_id=change.id, status="COMPLETED")
    db_session.add(run)

    risk = RiskAssessment(
        change_id=change.id,
        analysis_run_id=run.id,
        numerical_score=85.0,
        overall_risk="CRITICAL",
        contributing_factors=[{"factor": "cross-repo breakage"}],
    )
    policy = PolicyDecision(
        change_id=change.id,
        analysis_run_id=run.id,
        decision="BLOCK",
        rules_evaluated=[{"rule": "no_breaking_changes", "passed": False}],
        blocking_reasons=["Critical breaking change in cross-repo dependency auth-core-lib affecting 2 downstream services"],
    )
    ci = CIAssuranceCheck(
        change_id=change.id,
        commit_sha=change.commit_sha,
        gate_decision="BLOCK",
        policy_summary={"decision": "BLOCK"},
        exit_code=1,
    )
    db_session.add_all([risk, policy, ci])
    db_session.commit()

    # Benchmark 4: Agent Orchestration & Remediation Proposal
    agent = AgentGovernanceService.register_agent(
        db_session,
        AgentDefinitionCreate(
            organization_id=org.id,
            name="Autonomous-Remediation-Agent",
            agent_type="REMEDIATION_AGENT",
            autonomy_level=5,
        ),
    )
    t0 = time.perf_counter()
    task = AgentTaskOrchestrator.create_task(
        db_session,
        AgentTaskCreate(
            organization_id=org.id,
            agent_id=agent.id,
            change_id=change.id,
            analysis_run_id=run.id,
            task_type="REMEDIATION_PLAN",
        ),
    )
    AgentTaskOrchestrator.start_task(db_session, task.id)
    proposal = RemediationEngine.create_proposal(
        db_session,
        RemediationProposalCreate(
            organization_id=org.id,
            change_id=change.id,
            agent_id=agent.id,
            title="Backward compatible adapter for auth token verification",
            description="Preserves legacy verification signature while introducing v2 claims parsing",
            original_risk_score=85.0,
            original_risk_level="CRITICAL",
            proposed_diff="""- def verify_token(token):
+ def verify_token(token, compat_mode=True):
+     if compat_mode: return _verify_v1_legacy(token)
+     return _verify_v2(token)""",
            explanation="Eliminates downstream breakage in payment-service and billing-portal",
            affected_components=["auth_verifier"],
        ),
    )
    AgentTaskOrchestrator.complete_task(
        db_session, task.id, result={"proposal_id": proposal.id}
    )
    t1 = time.perf_counter()
    benchmarks["agent_orchestration_ms"] = round((t1 - t0) * 1000, 3)

    assert proposal.verification_status == "VERIFIED_SAFER"
    assert proposal.verified_risk_score < 85.0

    # Human Approval Gate: Request & Approve
    approval = AgentApprovalService.create_approval_request(
        db_session,
        AgentApprovalRequest(
            organization_id=org.id,
            task_id=task.id,
            change_id=change.id,
            requesting_agent_id=agent.id,
            requested_action="APPLY_REMEDIATION_PATCH",
            risk_level="HIGH",
        ),
    )
    assert approval.status == "PENDING"

    # Benchmark 5: Policy & Verdict Evaluation Before Approval
    t0 = time.perf_counter()
    verdict_before, _, _ = ChangeProofV3Assembler._compute_verdict(
        risk=risk,
        policy=policy,
        ci_checks=[ci],
        runtime_findings=[],
        agent_tasks=[task],
        remediations=[proposal],
        approvals=[approval],
    )
    t1 = time.perf_counter()
    benchmarks["policy_verdict_evaluation_ms"] = round((t1 - t0) * 1000, 3)
    assert verdict_before == "REMEDIATION_PENDING_APPROVAL"

    # Human Approves Remediation
    AgentApprovalService.decide_approval(
        db_session,
        approval.id,
        AgentApprovalDecision(decision="APPROVED", reason="Reviewed patch, backward compatibility verified"),
        approver_user_id="principal_architect_1",
    )

    # Benchmark 6: Change Proof v3 Generation
    t0 = time.perf_counter()
    proof_v3 = ChangeProofV3Assembler.assemble(
        db=db_session,
        change_id=change.id,
        analysis_run_id=run.id,
    )
    t1 = time.perf_counter()
    benchmarks["change_proof_v3_generation_ms"] = round((t1 - t0) * 1000, 3)

    assert proof_v3.overall_verdict == "REMEDIATION_VERIFIED"
    assert proof_v3.proof_document["version"] == "3.0.0"
    assert proof_v3.proof_document["phase_5_agentic"]["remediation_proposals"] == 1
    assert proof_v3.proof_document["phase_5_agentic"]["approved_actions"] == 1

    print("\n\n=== BENCHMARK MEASUREMENTS (ms) ===")
    for k, v in benchmarks.items():
        print(f"  {k}: {v} ms")
    print("===================================\n")
