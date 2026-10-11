# ADR 0008: SHA-256 Hash-Chained, Append-Oriented Immutable Audit Ledger

- Status: Accepted
- Date: 2026-10-11

## Context
Phase 5 lets AI/autonomous agents take consequential actions (read repos, generate tests, propose patches, request PRs). For "policy decides" to be trustworthy, every agent action — allowed, blocked, pending-approval, or failed — must be recorded in an audit trail that is append-oriented and tamper-evident, so no action can be silently inserted, altered, or removed after the fact. "Audit tampering" is an explicit threat the platform must control.

## Decision
Record every agent tool call and operation as an immutable entry in an append-oriented action ledger (`AgentAction` model + `AgentActionLedger` in `backend/app/services/enterprise/agent_service.py`). The ledger exposes only create/read operations (no update or delete), capturing agent, task, org/repo/change scope, requested capability, tool, input/output summaries, policy decision, status, and timestamp. Tamper evidence is provided by a per-organization **SHA-256 hash chain**: each entry stores a `chain_index`, the `previous_hash`, and an `entry_hash` computed over its canonical immutable fields plus the predecessor's hash (`_compute_entry_hash` / `record_action`). `verify_chain` recomputes the chain and reports the first entry at which it breaks; the integrity check is exposed at `GET /api/v1/agents/ledger/verify`.

## Consequences
### Positive
- Complete, append-only forensic record: every governed action (including BLOCKED and FAILED attempts) is persisted and chained.
- Any retroactive edit, reorder, or deletion of a historical entry changes a hash and is detected by `verify_chain` (covered by `tests/backend/unit/test_agent_ledger_hash_chain.py`).
- Per-task audit summaries aggregate allowed/blocked/succeeded/failed actions and tools used.
- Chains are isolated per organization, consistent with multi-tenant isolation (ADR 0009).
### Negative / Trade-offs
- Hash columns are schema-additive (migration `005_agent_ledger_hash_chain`) and nullable, so rows written before the chain existed are not retro-sealed.
- The chain detects tampering but does not prevent it; a privileged operator could rewrite the entire chain. A WORM store or managed ledger DB would be required for prevention (deferred, see Alternatives).
- Chaining serializes writes per organization and complicates any future partitioning of the ledger.
### Alternatives considered
- Plain mutable audit rows: rejected; offers no tamper evidence for a security-sensitive agent trail.
- External append-only log/WORM store or managed ledger DB (e.g., QLDB): rejected for now as added infra (consistent with ADR 0007); revisit under a measured compliance need.
- Full Merkle tree over entries: rejected as overkill for a linear action stream; a hash chain is sufficient.
