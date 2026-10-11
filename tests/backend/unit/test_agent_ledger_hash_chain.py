"""
Phase 5 — Tamper-evident agent action ledger (SHA-256 hash chain) tests.

Verifies that the agent action ledger forms a per-organization hash chain and
that retroactive tampering with a historical record is detectable.
"""
import pytest

from app.models.agent import AgentAction
from app.schemas.agent import AgentDefinitionCreate, AgentTaskCreate, AgentActionCreate
from app.services.enterprise import (
    AgentGovernanceService,
    AgentTaskOrchestrator,
    AgentActionLedger,
)


def _seed_task(db_session, org="org_chain"):
    agent = AgentGovernanceService.register_agent(
        db_session,
        AgentDefinitionCreate(organization_id=org, name="Chain-Worker",
                              agent_type="REMEDIATION_AGENT", autonomy_level=4),
    )
    task = AgentTaskOrchestrator.create_task(
        db_session,
        AgentTaskCreate(organization_id=org, agent_id=agent.id,
                        change_id="ch_chain", analysis_run_id="run_chain"),
    )
    return agent, task


def _record(db_session, agent, task, org, tool, decision="ALLOWED", status="SUCCESS"):
    return AgentActionLedger.record_action(
        db_session,
        AgentActionCreate(
            task_id=task.id, agent_id=agent.id, organization_id=org,
            repository_id="repo_chain", change_id="ch_chain", analysis_run_id="run_chain",
            action_type="READ", requested_capability="READ_REPOSITORY", tool_name=tool,
            input_summary={"target": tool}, output_summary={"status": status.lower()},
            policy_decision=decision, status=status,
        ),
    )


def test_first_entry_is_genesis_and_hashed(db_session):
    agent, task = _seed_task(db_session)
    action = _record(db_session, agent, task, "org_chain", "read_file")
    assert action.previous_hash == "GENESIS"
    assert action.entry_hash and len(action.entry_hash) == 64


def test_entries_are_chained(db_session):
    agent, task = _seed_task(db_session)
    a1 = _record(db_session, agent, task, "org_chain", "read_file")
    a2 = _record(db_session, agent, task, "org_chain", "ast_diff")
    assert a2.previous_hash == a1.entry_hash
    assert a2.entry_hash != a1.entry_hash


def test_verify_chain_valid_for_untampered_ledger(db_session):
    agent, task = _seed_task(db_session)
    for tool in ("read_file", "ast_diff", "pytest_runner"):
        _record(db_session, agent, task, "org_chain", tool)
    report = AgentActionLedger.verify_chain(db_session, "org_chain")
    assert report["valid"] is True
    assert report["length"] == 3
    assert report["broken_at"] is None


def test_tampering_breaks_the_chain(db_session):
    agent, task = _seed_task(db_session)
    _record(db_session, agent, task, "org_chain", "read_file")
    tampered = _record(db_session, agent, task, "org_chain", "ast_diff")
    _record(db_session, agent, task, "org_chain", "pytest_runner")

    # Retroactively alter a historical record without updating its hash.
    row = db_session.query(AgentAction).filter(AgentAction.id == tampered.id).one()
    row.policy_decision = "BLOCKED"
    db_session.commit()

    report = AgentActionLedger.verify_chain(db_session, "org_chain")
    assert report["valid"] is False
    assert report["broken_at"] == tampered.id


def test_chains_are_isolated_per_organization(db_session):
    agent_a, task_a = _seed_task(db_session, org="org_a")
    agent_b, task_b = _seed_task(db_session, org="org_b")
    _record(db_session, agent_a, task_a, "org_a", "read_file")
    first_b = _record(db_session, agent_b, task_b, "org_b", "read_file")
    # org_b's first entry is its own genesis, independent of org_a.
    assert first_b.previous_hash == "GENESIS"
    assert AgentActionLedger.verify_chain(db_session, "org_a")["valid"] is True
    assert AgentActionLedger.verify_chain(db_session, "org_b")["valid"] is True
