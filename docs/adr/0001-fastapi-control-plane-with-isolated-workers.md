# ADR 0001: Modular FastAPI Control Plane with Isolated Background Workers

- Status: Accepted
- Date: 2026-10-11

## Context
ProofMesh's thesis is "AI proposes, evidence verifies, policy decides," delivered through a staged 5-phase design where each phase layers more assurance onto an analyzed change. Analysis is slow and bursty (parsing, graph traversal, AI inference, policy evaluation), so it must not block the synchronous API that ingests changes and serves results. The product needed correctness and clear phase boundaries before any distributed-systems complexity.

## Decision
Build a single modular FastAPI control plane (`backend/app`, organized into `api/`, `services/`, `repositories/`, `models/`) that enqueues analysis jobs onto a Redis queue, and run the heavy assurance pipeline in a separate, independently deployable worker process (`backend/app/workers/worker.py`) that pops jobs via a blocking `BLPOP` and drives the staged pipeline (INGESTION_VALIDATION → CODE_ANALYSIS → IMPACT_ANALYSIS → AI_ASSURANCE → RISK_ASSESSMENT → POLICY_EVALUATION). Workers and API share the same codebase and database but run as distinct containers in Docker Compose.

## Consequences
### Positive
- API stays responsive; long analyses run out-of-band with per-stage status and audit logging.
- Workers scale horizontally (stateless, queue-driven) without touching the API tier.
- Built-in resilience: failed jobs retry with incrementing `attempt` up to `max_attempts` before terminal FAILED.
- One codebase keeps domain logic, schemas, and migrations consistent across API and worker.
### Negative / Trade-offs
- Redis becomes a required runtime dependency and a potential single point of failure for job dispatch.
- A shared code/database boundary means API and worker are coupled at deploy time (not true service autonomy).
- At-least-once delivery requires idempotency awareness in pipeline stages.
### Alternatives considered
- Microservices per phase up front: rejected as premature; adds network, versioning, and operational cost before product correctness is proven.
- In-process background tasks (FastAPI `BackgroundTasks`/threads): rejected because CPU-heavy analysis would degrade API latency and could not scale independently.
- A full broker/orchestrator (Celery, Kafka): rejected as over-engineered for current scope (see ADR 0007).
