# ProofMesh — Architecture Documentation (Phase 1)

## 1. System Overview

ProofMesh is structured as a modular, asynchronous change assurance system designed around clean boundaries, explicit schemas, transactional integrity, and idempotency.

```text
                     +---------------------------------------+
                     |         React + TypeScript UI         |
                     | (Vite, Tailwind, Modern Dark System)  |
                     +-------------------+-------------------+
                                         |
                                     REST API
                                         |
                                         v
                     +---------------------------------------+
                     |            FastAPI Backend            |
                     |  - API Routing (/api/v1)              |
                     |  - Request Correlation (Request ID)   |
                     |  - JWT Auth & RBAC Guards             |
                     |  - Webhook Ingestion & HMAC Verify    |
                     |  - Structured JSON Logging            |
                     +-------------------+-------------------+
                                         |
                  +----------------------+----------------------+
                  |                      |                      |
                  v                      v                      v
        +------------------+   +------------------+   +------------------+
        |    PostgreSQL    |   |   Redis Queue    |   |    GitHub API    |
        |  (Relational DB) |   | (Job Broker)     |   | (App Integration)|
        +--------+---------+   +--------+---------+   +------------------+
                 |                      |
                 |                      v
                 |             +------------------+
                 |             | Analysis Worker  |
                 +<------------+ (Async Consumer) |
                               +------------------+
```

---

## 2. Component Descriptions

### 2.1 FastAPI Backend
- **Core Principles**: API-First, layered architecture (`Router` -> `Service` -> `Repository` -> `Database`).
- **Middleware**:
  - `RequestIdMiddleware`: generates or propagates `X-Request-ID` across every incoming request and downstream response.
  - `CORSMiddleware`: enforces strict origins (`http://localhost:5173`, etc.).
  - Global standardized error envelopes (`code`, `message`, `request_id`, `details`).

### 2.2 PostgreSQL Database
- Relational persistence with foreign keys, compound uniqueness constraints, and explicit indices.
- Entities:
  - `users`, `organizations`, `user_organization_memberships`
  - `repositories`, `pull_requests`, `changes`, `analysis_runs`
  - `audit_logs`, `processed_webhook_events`

### 2.3 Redis Queue & Background Worker
- Asynchronous task processing decoupled from HTTP request loops.
- Queue payload contains `change_id`, `analysis_run_id`, `attempt`, `max_attempts`.
- Worker lifecycle state machine:
  `QUEUED` -> `RUNNING` -> `INGESTION_VALIDATION` -> `COMPLETED` (or retry/`FAILED`).

### 2.4 GitHub App & Webhook Ingestion
- Ingests `pull_request` events (`opened`, `synchronize`, `reopened`, `closed`).
- HMAC-SHA256 signature verification via `X-Hub-Signature-256`.
- Idempotency verified using `X-GitHub-Delivery` ledger.

### 2.5 React + TypeScript Frontend
- Built with Vite, TypeScript, Tailwind CSS, Lucide icons.
- Responsive engineering dashboard, repositories list/detail, changes explorer, change detail with visual lifecycle timeline and audit streams.
