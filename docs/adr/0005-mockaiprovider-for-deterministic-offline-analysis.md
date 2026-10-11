# ADR 0005: MockAIProvider for Deterministic, Offline Analysis

- Status: Accepted
- Date: 2026-10-11

## Context
Phase 3 assurance uses AI to propose change intent, behavioral invariants, security findings, and test recommendations — the "AI proposes" half of the thesis. But a resume-grade demo and its benchmark must be reproducible, run offline, cost nothing, and never leak secrets, while still leaving a clean path to a real LLM later. Depending on a live model for every analysis would make tests flaky, expensive, and non-deterministic.

## Decision
Define an abstract `AIProvider` interface (`backend/app/services/assurance/ai_provider.py`) with four capabilities (`infer_intent`, `propose_invariants`, `analyze_security`, `recommend_tests`) and ship a deterministic `MockAIProvider` as the default, selected via `ProviderFactory.get_provider()`. The mock derives structured, schema-shaped output from diff/metadata signals and runs diff input through `SecretRedactor` before inference. Each result carries provenance (`model_info`: provider, model, version, prompt_version, latency) and confidence scores.

## Consequences
### Positive
- Analysis and the benchmark are fully reproducible, run offline, and cost $0.
- Clean seam: a real provider (OpenAI/Anthropic/Google) can be added behind the same interface without touching the pipeline.
- Every AI output is structured with explicit provenance and confidence, feeding the downstream policy engine cleanly.
- Secret redaction at the provider boundary reduces the risk of leaking credentials into stored evidence.
### Negative / Trade-offs
- The mock's heuristics are shallow (keyword/pattern matching), so it does not reflect real model quality.
- Risk of the interface quietly drifting from what real providers need until a live provider is actually wired in.
- Redaction is currently applied at the mock's input boundary; full-coverage redaction/validation of every field would need enforcement in the orchestrator/schema layer.
### Alternatives considered
- Call a real LLM directly in the pipeline: rejected; non-deterministic, costly, requires network/keys, breaks offline tests.
- Record/replay fixtures of real responses: rejected; brittle and heavier to maintain than a deterministic generator for a demo.
- No abstraction, hard-coded mock: rejected; would make swapping in a real model a rewrite rather than a config change.
