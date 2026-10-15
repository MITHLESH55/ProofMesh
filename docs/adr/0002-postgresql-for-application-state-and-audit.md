# ADR 0002: PostgreSQL for Application State and Audit

- Status: Accepted
- Date: 2026-10-11

## Context
ProofMesh must persist strongly relational, multi-tenant state — organizations, repositories, pull requests, changes, analysis runs, risk assessments, policy decisions, change proofs, and audit logs — while supporting the "evidence verifies, policy decides" thesis, which demands durable, consistent, auditable records. Across the 5-phase design these entities accumulate foreign-key relationships and must survive restarts and support reproducible queries.

## Decision
Use PostgreSQL as the system of record for all relational application and audit state, accessed through SQLAlchemy 2.0 ORM models (`backend/app/models/`) with schema evolution managed by Alembic migrations (`backend/alembic/`). The runtime driver is `psycopg2` against `postgresql+psycopg2://...` (PostgreSQL 15 in Docker Compose).

## Consequences
### Positive
- ACID transactions give consistent writes across pipeline stages (e.g., change status + analysis run + audit log committed together).
- Mature relational modeling, foreign-key integrity, and indexing fit the tenant/repo/change hierarchy.
- Alembic provides versioned, reviewable migrations for safe schema evolution across phases.
- JSON columns allow semi-structured evidence (proof documents, plans, embeddings) without abandoning relational guarantees.
### Negative / Trade-offs
- Graph-shaped dependency traversal is awkward in SQL, which is why that workload is delegated to Neo4j (see ADR 0003).
- A single relational store can become a scaling bottleneck under very high write volume.
- Migrations must be disciplined; drift between models and migrations causes startup failures.
### Alternatives considered
- NoSQL document store (MongoDB): rejected because the domain is inherently relational and audit integrity benefits from ACID and FKs.
- SQLite: rejected; insufficient for concurrent multi-worker writes and multi-tenant production use.
- Storing audit logs only in append-only files: rejected; queryability and joins with domain entities are required.
