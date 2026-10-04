# ProofMesh — Phase 1 Specification: Foundation & Change Ingestion

## 1. Objective

Phase 1 establishes the production-grade foundation and trustworthy boundary around software-change ingestion for ProofMesh.

It provides a fully working, containerized system capable of:
1. Receiving signed GitHub Pull Request webhook events (`opened`, `synchronize`, `reopened`, `closed`).
2. Validating HMAC-SHA256 signatures with constant-time equality comparisons.
3. Enforcing event idempotency using unique delivery ID tracking.
4. Persisting Organizations, Users, Repositories, Pull Requests, Changes, and Analysis Runs in PostgreSQL.
5. Asynchronously enqueuing and processing analysis jobs via Redis and background worker processes.
6. Recording audit logs across all lifecycle events.
7. Exposing REST APIs for authentication, RBAC, repository management, change tracking, and health checks.
8. Providing a responsive React + TypeScript frontend dashboard with real-time pipeline status and visual lifecycle timelines.

---

## 2. Implemented Architecture

```text
GitHub
   │ (Webhook HTTP POST)
   ▼
POST /api/v1/webhooks/github
   │
   ├─► 1. HMAC-SHA256 Signature Verification (X-Hub-Signature-256)
   ├─► 2. Delivery Idempotency Check (X-GitHub-Delivery)
   ├─► 3. Atomic DB Transaction:
   │      - Organization / Repository lookup or creation
   │      - Pull Request entity update / creation
   │      - Change entity mapping commit SHA
   │      - Analysis Run initialization (status: QUEUED)
   │      - Audit log emissions
   │
   ▼
Redis Analysis Queue (proofmesh:queue:analysis)
   │
   ▼
Background Analysis Worker
   │
   ├─► 1. Status: RUNNING (records worker_id, started_at)
   ├─► 2. Ingestion Validation (PR & Commit SHA integrity)
   └─► 3. Status: COMPLETED (records completed_at, audit log)
   │
   ▼
FastAPI Backend (REST API /api/v1)
   │
   ▼
React + TypeScript Frontend Dashboard
```

---

## 3. Database Schema

- **`users`**: User identities, bcrypt password hashes, global roles (`ADMIN`, `ENGINEER`, `VIEWER`), active flags.
- **`organizations`**: Multi-tenant organizations with unique slugs.
- **`user_organization_memberships`**: RBAC memberships associating users with organizations.
- **`repositories`**: GitHub repositories tracked by GitHub ID, owner, name, and default branch.
- **`pull_requests`**: Pull requests with number, title, author, head SHA, base SHA, state (`OPEN`, `CLOSED`, `MERGED`).
- **`changes`**: Software change objects representing specific commit SHAs attached to pull requests.
- **`analysis_runs`**: Asynchronous run execution records (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`).
- **`audit_logs`**: Immutable audit logs capturing user/system actions and JSON metadata.
- **`processed_webhook_events`**: Idempotency ledger storing processed GitHub delivery IDs.

---

## 4. Known Limitations & Phase 2 Boundaries

In accordance with Phase 1 constraints:
- **No AST / Semantic Code Analysis**: Phase 1 validates ingestion metadata only. Deep syntax and semantic analysis will be introduced in Phase 2.
- **No Risk Scoring**: Fake or arbitrary risk numbers are intentionally omitted.
- **No Repository Code Execution**: Worker processes only ingest and validate change metadata; user code is never executed in worker runtime.
