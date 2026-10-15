# ADR 0009: Tiered Agent Autonomy and Governance Framework

- Status: Accepted
- Date: 2026-10-11

## Context
Phase 5 introduces autonomous and AI-agent-initiated changes. "AI proposes, evidence verifies, policy decides" must extend to agents themselves: an agent must only ever do what it is explicitly permitted to, within its tenant, under hard safety limits, and never be able to self-authorize high-risk actions. Unbounded agents are a safety, cost, and multi-tenant-isolation hazard.

## Decision
Govern agents with a tiered autonomy framework (`AgentGovernanceService` and related classes in `backend/app/services/enterprise/agent_service.py`). Autonomy levels 0–5 (Observe → Analyze → Generate Artifacts → Create PRs → Operational → Autonomous) map to escalating capability tiers; a frozen set of hard-denied capabilities (e.g., `MODIFY_PRODUCTION_DB`, `BYPASS_POLICY`, `ESCALATE_PRIVILEGES`) is refused at every level. Per-task budgets bound steps, tokens, cost, runtime, retries, and model calls (auto-terminating on breach); `check_scope` enforces tenant and repository isolation; high-risk capabilities require human approval; and an agent is forbidden from approving its own action.

## Consequences
### Positive
- Capabilities are capped by autonomy level and intersected against hard-deny rules, so over-privileged registration is impossible.
- Budget enforcement bounds runaway cost/looping (auto `BUDGET_EXCEEDED` termination).
- Tenant/repo scope checks prevent cross-tenant access; self-approval guard preserves human-in-the-loop integrity.
- Every authorization decision is explainable and recorded in the action ledger (see ADR 0008).
### Negative / Trade-offs
- The framework exposes six discrete levels (0–5); the mapping of real agent behaviors to a tier is a human judgment call.
- Input/prompt-injection sanitization at the agent boundary is a stated governance goal but is not yet implemented in this service (secret redaction exists only in the Phase 3 AI-provider layer), leaving that threat under-controlled today.
- Static tiers and fixed numeric budgets are coarse and may need per-org tuning.
### Alternatives considered
- Single on/off "autonomous" switch: rejected; too coarse to safely stage trust.
- Trust the agent/LLM to self-limit via prompt: rejected; not enforceable and not auditable.
- No budget ceilings: rejected; invites runaway cost and infinite loops.
