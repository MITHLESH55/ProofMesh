# ADR 0010: Change Proof as the Central Auditable Artifact

- Status: Accepted
- Date: 2026-10-11

## Context
ProofMesh's thesis — "AI proposes, evidence verifies, policy decides" — only has value if the verification and decision are captured in a single, machine-readable artifact that a human or system can inspect and audit. Scattering intent, impact, invariants, contracts, security findings, tests, risk, evidence, and the final decision across endpoints would make a change's safety story impossible to reproduce or trust across the 5-phase pipeline.

## Decision
Make the Change Proof the system's primary output and central audit object. `ChangeProofBuilder` (`backend/app/services/assurance/change_proof_builder.py`) compiles a structured v1 artifact answering ten questions (what/why changed, blast radius, behavioral invariants, semantic contracts, security, tests, explainable risk, evidence ledger, policy decision) plus a fast-inspection summary. The artifact is versioned and evolves across phases: v1 (Phase 3 static assurance), through to Change Proof v3 (`ChangeProofV3Assembler`), which unifies Phase 3 static, Phase 4 CI/runtime, and Phase 5 agentic signals into one canonical verdict.

## Consequences
### Positive
- One self-contained, machine-readable artifact tells a change's complete safety story, including an explicit policy decision and uncertainties.
- Explicit versioning (v1 → v3) lets the proof grow with new assurance phases without breaking consumers of earlier versions.
- The proof doubles as the durable audit record and the input to historical evidence/learning (see ADR 0006).
- Numbered sections and a summary make it directly consumable by UI, API, and reviewers.
### Negative / Trade-offs
- Multiple proof versions coexist (v1 artifact dict and the persisted `ChangeProofV3`), so consumers must be version-aware.
- A large aggregate artifact couples many producers; a schema change ripples across builders and readers.
- Proof fidelity is bounded by the quality of upstream analysis — a thin analysis yields a thin (but honest) proof.
### Alternatives considered
- Expose findings only through separate endpoints with no unified artifact: rejected; not auditable or reproducible as a single object.
- A free-form text report: rejected; not machine-readable or diffable across versions.
- Overwrite one proof schema in place as phases evolve: rejected; explicit versioning preserves backward compatibility and historical comparability.
