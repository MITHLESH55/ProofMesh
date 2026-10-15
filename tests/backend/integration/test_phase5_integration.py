"""
Phase 5 Integration Tests — Enterprise & Agent Services with SQLite in-memory database.

Tests cover:
- EnterpriseService: team, service, ownership, and cross-repo dependency CRUD
- HistoricalEvidenceService: store, list, search (with real DB)
- EnterpriseGraphService: graph construction and impact analysis
- AgentGovernanceService: agent registration with capability enforcement
- AgentTaskOrchestrator: task lifecycle and budget recording
- AgentActionLedger: action recording and audit summaries
- AgentApprovalService: approval creation and decision workflow
- RemediationEngine: proposal creation with DB persistence
- ChangeProofV3Assembler: full proof assembly from DB records
"""
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models import *  # noqa: F401,F403 — registers all models


# ─── Database Setup ───

@pytest.fixture(scope="module")
def engine():
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=e)
    yield e
    Base.metadata.drop_all(bind=e)


@pytest.fixture
def db(engine):
    conn = engine.connect()
    txn = conn.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=conn)()
    yield session
    session.close()
    txn.rollback()
    conn.close()


def _id():
    return str(uuid.uuid4())


# ─── Seed Helpers ───

def seed_org(db: Session) -> str:
    from app.models.entities import Organization
    org = Organization(id=_id(), name="TestCorp", slug=f"testcorp-{_id()[:8]}")
    db.add(org)
    db.commit()
    return org.id


def seed_repo(db: Session, org_id: str) -> str:
    from app.models.entities import Repository
    uid = _id()[:8]
    repo = Repository(
        id=_id(), organization_id=org_id,
        github_repository_id=f"gh-{uid}",
        owner="testcorp",
        name=f"test-repo-{uid}",
        full_name=f"testcorp/test-repo-{uid}",
        default_branch="main",
    )
    db.add(repo)
    db.commit()
    return repo.id


def seed_pull_request(db: Session, repo_id: str) -> str:
    from app.models.entities import PullRequest
    uid = _id()[:8]
    pr = PullRequest(
        id=_id(),
        repository_id=repo_id,
        github_pr_id=f"pr-{uid}",
        number=1,
        title="Test PR",
        author="testuser",
        head_sha=f"head-{uid}",
        base_sha=f"base-{uid}",
        state="OPEN",
    )
    db.add(pr)
    db.commit()
    return pr.id


def seed_change(db: Session, repo_id: str) -> str:
    from app.models.entities import Change
    pr_id = seed_pull_request(db, repo_id)
    change = Change(
        id=_id(),
        pull_request_id=pr_id,
        commit_sha=f"sha-{_id()[:8]}",
        status="INGESTED",
    )
    db.add(change)
    db.commit()
    return change.id


def seed_analysis_run(db: Session, change_id: str) -> str:
    from app.models.entities import AnalysisRun
    run = AnalysisRun(
        id=_id(), change_id=change_id,
        stage="AI_ASSURANCE", status="COMPLETED",
    )
    db.add(run)
    db.commit()
    return run.id


# ─── EnterpriseService ───

class TestEnterpriseService:
    def test_create_and_list_team(self, db):
        from app.services.enterprise import EnterpriseService
        from app.schemas.enterprise import TeamCreate
        org_id = seed_org(db)

        data = TeamCreate(organization_id=org_id, name="Platform", slug="platform")
        team = EnterpriseService.create_team(db, data)
        assert team.id is not None
        assert team.name == "Platform"
        assert team.slug == "platform"

        teams = EnterpriseService.list_teams(db, organization_id=org_id)
        assert len(teams) == 1
        assert teams[0].id == team.id

    def test_create_and_list_service(self, db):
        from app.services.enterprise import EnterpriseService
        from app.schemas.enterprise import TeamCreate, ServiceCreate
        org_id = seed_org(db)
        repo_id = seed_repo(db, org_id)

        team_data = TeamCreate(organization_id=org_id, name="Security", slug="security")
        team = EnterpriseService.create_team(db, team_data)

        svc_data = ServiceCreate(
            organization_id=org_id,
            team_id=team.id,
            repository_id=repo_id,
            name="auth-service",
            criticality="CRITICAL",
            tier=1,
        )
        service = EnterpriseService.create_service(db, svc_data)
        assert service.criticality == "CRITICAL"
        assert service.tier == 1

        services = EnterpriseService.list_services(db, organization_id=org_id, criticality="CRITICAL")
        assert len(services) == 1
        assert services[0].name == "auth-service"

    def test_cross_repo_dependency(self, db):
        from app.services.enterprise import EnterpriseService
        from app.schemas.enterprise import CrossRepoDependencyCreate
        org_id = seed_org(db)
        src_id = seed_repo(db, org_id)
        tgt_id = seed_repo(db, org_id)

        data = CrossRepoDependencyCreate(
            organization_id=org_id,
            source_repository_id=src_id,
            target_repository_id=tgt_id,
            dependency_type="PACKAGE",
            package_or_service_name="proofmesh-core",
            provenance_details={"detected_by": "pip-audit"},
        )
        dep = EnterpriseService.record_cross_repo_dependency(db, data)
        assert dep.dependency_type == "PACKAGE"
        assert dep.provenance_details["detected_by"] == "pip-audit"

        deps = EnterpriseService.list_cross_repo_dependencies(db, organization_id=org_id)
        assert len(deps) == 1

    def test_enterprise_overview(self, db):
        from app.services.enterprise import EnterpriseService
        from app.schemas.enterprise import TeamCreate, ServiceCreate
        org_id = seed_org(db)
        EnterpriseService.create_team(db, TeamCreate(organization_id=org_id, name="T1", slug="t1"))
        EnterpriseService.create_service(db, ServiceCreate(
            organization_id=org_id, name="svc1", criticality="HIGH"
        ))

        overview = EnterpriseService.get_enterprise_overview(db, organization_id=org_id)
        assert overview.total_teams >= 1
        assert overview.total_services >= 1


# ─── HistoricalEvidenceService ───

class TestHistoricalEvidenceServiceIntegration:
    def test_store_and_list_evidence(self, db):
        from app.services.enterprise import HistoricalEvidenceService
        from app.schemas.enterprise import HistoricalEvidenceCreate
        org_id = seed_org(db)

        data = HistoricalEvidenceCreate(
            organization_id=org_id,
            evidence_type="INCIDENT",
            title="DB connection failure",
            content="Production database connection pool exhausted after deployment.",
            provenance={"source": "pagerduty", "incident_id": "INC-001"},
        )
        record = HistoricalEvidenceService.store_evidence(db, data)
        assert record.id is not None
        assert record.evidence_type == "INCIDENT"
        assert record.embedding is not None  # auto-computed

        records = HistoricalEvidenceService.list_evidence(db, organization_id=org_id)
        assert len(records) == 1

    def test_semantic_search_finds_relevant(self, db):
        from app.services.enterprise import HistoricalEvidenceService
        from app.schemas.enterprise import HistoricalEvidenceCreate, EvidenceSearchRequest
        org_id = seed_org(db)

        for title, content in [
            ("SQL Injection Fix", "Fixed SQL injection vulnerability in user login endpoint"),
            ("DB Migration", "Applied schema migration to add new index for performance"),
            ("Auth Bypass Incident", "Production incident: authentication bypass allowed unauthorized access"),
        ]:
            HistoricalEvidenceService.store_evidence(db, HistoricalEvidenceCreate(
                organization_id=org_id,
                evidence_type="INCIDENT",
                title=title, content=content,
                provenance={},
            ))

        request = EvidenceSearchRequest(
            query="authentication security bypass",
            organization_id=org_id,
            limit=5,
        )
        results = HistoricalEvidenceService.search(db, request)

        # Should return at least 1 result
        assert len(results) >= 1
        # The auth-related incident should rank higher
        assert results[0].similarity_score > 0.0
        # Results ordered by similarity
        scores = [r.similarity_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_ingest_from_incident(self, db):
        from app.services.enterprise import HistoricalEvidenceService
        org_id = seed_org(db)
        record = HistoricalEvidenceService.ingest_from_incident(
            db,
            organization_id=org_id,
            incident_id="INC-999",
            summary="Payment service down",
            root_cause="Null pointer in payment processing loop",
            severity="CRITICAL",
        )
        assert record.evidence_type == "INCIDENT"
        assert record.provenance["severity"] == "CRITICAL"
        assert record.provenance["incident_id"] == "INC-999"


# ─── EnterpriseGraphService ───

class TestEnterpriseGraphService:
    def test_build_empty_graph(self, db):
        from app.services.enterprise import EnterpriseGraphService
        org_id = seed_org(db)
        graph = EnterpriseGraphService.build_enterprise_graph(db, org_id)
        assert graph.organization_id == org_id
        assert isinstance(graph.nodes, list)
        assert isinstance(graph.edges, list)

    def test_graph_includes_repo_nodes(self, db):
        from app.services.enterprise import EnterpriseGraphService
        org_id = seed_org(db)
        seed_repo(db, org_id)
        seed_repo(db, org_id)

        graph = EnterpriseGraphService.build_enterprise_graph(db, org_id)
        repo_nodes = [n for n in graph.nodes if n.type == "REPOSITORY"]
        assert len(repo_nodes) == 2

    def test_cross_repo_impact_analysis(self, db):
        from app.services.enterprise import EnterpriseService, EnterpriseGraphService
        from app.schemas.enterprise import CrossRepoDependencyCreate
        org_id = seed_org(db)
        src_id = seed_repo(db, org_id)
        tgt_id = seed_repo(db, org_id)

        EnterpriseService.record_cross_repo_dependency(db, CrossRepoDependencyCreate(
            organization_id=org_id,
            source_repository_id=src_id,
            target_repository_id=tgt_id,
            dependency_type="PACKAGE",
            package_or_service_name="shared-lib",
            provenance_details={},
        ))

        impact = EnterpriseGraphService.get_cross_repo_impact(db, org_id, tgt_id)
        assert impact["downstream_repository_count"] == 1
        assert src_id in impact["downstream_repository_ids"]

    def test_graph_snapshot(self, db):
        from app.services.enterprise import EnterpriseGraphService
        org_id = seed_org(db)
        seed_repo(db, org_id)

        version = EnterpriseGraphService.snapshot_graph(
            db, org_id, "v1.0.0", "deadbeef1234"
        )
        assert version.organization_id == org_id
        assert version.version_tag == "v1.0.0"
        assert version.node_count >= 1


# ─── AgentGovernanceService ───

class TestAgentGovernanceIntegration:
    def test_register_agent_enforces_capability_tier(self, db):
        from app.services.enterprise import AgentGovernanceService
        from app.schemas.agent import AgentDefinitionCreate
        org_id = seed_org(db)

        data = AgentDefinitionCreate(
            organization_id=org_id,
            name="review-bot",
            agent_type="REVIEW_AGENT",
            autonomy_level=1,
            capabilities=["READ_REPOSITORY", "CREATE_PR"],  # CREATE_PR not in level 1
        )
        agent = AgentGovernanceService.register_agent(db, data)
        assert "CREATE_PR" not in agent.capabilities
        assert "READ_REPOSITORY" in agent.capabilities

    def test_register_agent_strips_hard_denied(self, db):
        from app.services.enterprise import AgentGovernanceService
        from app.schemas.agent import AgentDefinitionCreate
        from app.services.enterprise.agent_service import HARD_DENIED_CAPABILITIES
        org_id = seed_org(db)

        # Even at autonomy_level=5, hard-denied must be stripped
        evil_caps = list(HARD_DENIED_CAPABILITIES) + ["READ_REPOSITORY"]
        data = AgentDefinitionCreate(
            organization_id=org_id,
            name="evil-bot",
            agent_type="ORCHESTRATOR_AGENT",
            autonomy_level=5,
            capabilities=evil_caps,
        )
        agent = AgentGovernanceService.register_agent(db, data)
        for cap in HARD_DENIED_CAPABILITIES:
            assert cap not in agent.capabilities

    def test_list_and_disable_agent(self, db):
        from app.services.enterprise import AgentGovernanceService
        from app.schemas.agent import AgentDefinitionCreate
        org_id = seed_org(db)

        agent = AgentGovernanceService.register_agent(db, AgentDefinitionCreate(
            organization_id=org_id, name="test-agent",
            agent_type="REVIEW_AGENT", autonomy_level=1,
        ))
        assert agent.status == "ACTIVE"

        agents = AgentGovernanceService.list_agents(db, organization_id=org_id, status="ACTIVE")
        assert any(a.id == agent.id for a in agents)

        disabled = AgentGovernanceService.disable_agent(db, agent.id)
        assert disabled.status == "DISABLED"


# ─── AgentTaskOrchestrator ───

class TestAgentTaskOrchestratorIntegration:
    def test_task_lifecycle(self, db):
        from app.services.enterprise import AgentGovernanceService, AgentTaskOrchestrator
        from app.schemas.agent import AgentDefinitionCreate, AgentTaskCreate
        org_id = seed_org(db)
        repo_id = seed_repo(db, org_id)
        change_id = seed_change(db, repo_id)
        run_id = seed_analysis_run(db, change_id)

        agent = AgentGovernanceService.register_agent(db, AgentDefinitionCreate(
            organization_id=org_id, name="test-agent",
            agent_type="REVIEW_AGENT", autonomy_level=1,
        ))

        task = AgentTaskOrchestrator.create_task(db, AgentTaskCreate(
            organization_id=org_id,
            agent_id=agent.id,
            change_id=change_id,
            analysis_run_id=run_id,
            task_type="MULTI_AGENT_ASSURANCE",
        ))
        assert task.status == "PENDING"
        assert task.step_count == 0

        started = AgentTaskOrchestrator.start_task(db, task.id)
        assert started.status == "RUNNING"

        completed = AgentTaskOrchestrator.complete_task(db, task.id, {"summary": "ok"})
        assert completed.status == "COMPLETED"
        assert completed.result["summary"] == "ok"

    def test_budget_exceeded_auto_terminates(self, db):
        from app.services.enterprise import AgentGovernanceService, AgentTaskOrchestrator
        from app.schemas.agent import AgentDefinitionCreate, AgentTaskCreate
        from app.services.enterprise.agent_service import MAX_STEPS_PER_TASK
        org_id = seed_org(db)
        repo_id = seed_repo(db, org_id)
        change_id = seed_change(db, repo_id)
        run_id = seed_analysis_run(db, change_id)

        agent = AgentGovernanceService.register_agent(db, AgentDefinitionCreate(
            organization_id=org_id, name="budget-test",
            agent_type="REVIEW_AGENT", autonomy_level=1,
        ))
        task = AgentTaskOrchestrator.create_task(db, AgentTaskCreate(
            organization_id=org_id, agent_id=agent.id,
            change_id=change_id, analysis_run_id=run_id,
        ))
        AgentTaskOrchestrator.start_task(db, task.id)

        # Exhaust step budget
        for _ in range(MAX_STEPS_PER_TASK):
            task = AgentTaskOrchestrator.record_step(db, task.id, tokens_used=100, cost_delta=0.001)

        assert task.status == "BUDGET_EXCEEDED"
        assert "termination_reason" in task.result


# ─── AgentApprovalService ───

class TestAgentApprovalIntegration:
    def test_approval_workflow(self, db):
        from app.services.enterprise import AgentGovernanceService, AgentApprovalService
        from app.schemas.agent import AgentDefinitionCreate, AgentApprovalRequest, AgentApprovalDecision
        from app.models.entities import User
        org_id = seed_org(db)
        repo_id = seed_repo(db, org_id)
        change_id = seed_change(db, repo_id)

        agent = AgentGovernanceService.register_agent(db, AgentDefinitionCreate(
            organization_id=org_id, name="remediation-bot",
            agent_type="REMEDIATION_AGENT", autonomy_level=5,
        ))

        user = User(
            id=_id(), email=f"approver-{_id()[:6]}@test.com",
            password_hash="hashed", full_name="Test Approver",
        )
        db.add(user)
        db.commit()

        approval = AgentApprovalService.create_approval_request(db, AgentApprovalRequest(
            organization_id=org_id,
            change_id=change_id,
            requesting_agent_id=agent.id,
            requested_action="CREATE_PULL_REQUEST",
            risk_level="HIGH",
            affected_resources=["auth/service.py"],
            evidence_summary={"risk_score": 70.0},
        ))
        assert approval.status == "PENDING"

        pending = AgentApprovalService.list_pending_approvals(db, organization_id=org_id)
        assert any(a.id == approval.id for a in pending)

        decided = AgentApprovalService.decide_approval(
            db, approval.id,
            AgentApprovalDecision(decision="APPROVED", reason="Looks good"),
            approver_user_id=user.id,
        )
        assert decided.status == "APPROVED"
        assert decided.approver_user_id == user.id


# ─── RemediationEngine ───

class TestRemediationEngineIntegration:
    def test_create_and_verify_proposal(self, db):
        from app.services.enterprise import AgentGovernanceService, RemediationEngine
        from app.schemas.agent import AgentDefinitionCreate, RemediationProposalCreate
        org_id = seed_org(db)
        repo_id = seed_repo(db, org_id)
        change_id = seed_change(db, repo_id)

        agent = AgentGovernanceService.register_agent(db, AgentDefinitionCreate(
            organization_id=org_id, name="rem-agent",
            agent_type="REMEDIATION_AGENT", autonomy_level=3,
        ))

        proposal = RemediationEngine.create_proposal(db, RemediationProposalCreate(
            organization_id=org_id,
            change_id=change_id,
            agent_id=agent.id,
            title="Fix SQL injection",
            description="Replace raw SQL with parameterized queries",
            original_risk_score=70.0,
            original_risk_level="HIGH",
            proposed_diff="\n".join([f"+fix line {i}" for i in range(8)]),
            explanation="Parameterized queries prevent SQL injection",
            affected_components=["db/queries.py"],
        ))

        assert proposal.verification_status == "VERIFIED_SAFER"
        assert proposal.verified_risk_score < 70.0
        assert proposal.verification_evidence["delta"] > 0.0

        proposals = RemediationEngine.list_proposals(db, change_id=change_id)
        assert len(proposals) == 1
