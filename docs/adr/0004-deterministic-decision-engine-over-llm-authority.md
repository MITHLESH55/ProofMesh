# ADR 0004: Deterministic Decision Engine over LLM Authority

- Status: Accepted
- Date: 2026-10-11

## Context
ProofMesh's governing principle is "AI proposes, evidence verifies, policy decides." An LLM can be non-deterministic, confidently wrong, and prompt-manipulable, so it must never hold release authority. For an assurance platform, the final PASS/WARN/BLOCK verdict must be reproducible, explainable, and safe-by-default — and a missing or empty analysis must never silently resolve to PASS.

## Decision
Render the final governance decision in a deterministic, pure-function `PolicyEngine` (`backend/app/services/assurance/policy_engine.py`) that evaluates structured evidence (risk assessment, security findings, API contracts, behavioral invariants, evidence count) against explicit, identified rules (POL_001 Evidence Sufficiency, POL_002 No Critical Security, POL_003 Behavioral Invariants, POL_004 API Contract Compatibility, plus warning rules) and returns one of PASS / WARN / BLOCK / INSUFFICIENT_EVIDENCE with explicit blocking and warning reasons.

## Consequences
### Positive
- Decisions are deterministic and reproducible: the same evidence always yields the same verdict.
- Safe-by-default: zero evidence with no findings/contracts returns INSUFFICIENT_EVIDENCE, never PASS — closing the "silent pass" gap.
- Fully explainable: every decision carries `rules_evaluated` and human-readable reasons for audit.
- Any CRITICAL security finding, VIOLATED invariant, or BREAKING contract forces BLOCK regardless of AI confidence.
### Negative / Trade-offs
- Rules are hand-authored; new risk categories require explicit code/policy changes.
- Determinism can be rigid — nuanced edge cases the rules do not model fall through to WARN/PASS rather than human judgment.
- The engine is only as good as the evidence fed to it; weak upstream analysis still yields a weak (but honest) verdict.
### Alternatives considered
- Let the LLM output the final decision: rejected; non-deterministic, unauditable, and manipulable — incompatible with the thesis.
- ML-scored risk threshold as the gate: rejected; opaque and non-reproducible for governance/audit.
- No INSUFFICIENT_EVIDENCE state (binary pass/fail): rejected; would allow empty analyses to masquerade as passing.
