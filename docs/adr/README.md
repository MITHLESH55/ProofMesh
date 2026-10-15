# Architecture Decision Records (ADRs)

This directory records the significant architecture decisions behind **ProofMesh**, an AI-Native Software Change Assurance Platform (FastAPI backend + React/TypeScript frontend) built around the thesis **"AI proposes, evidence verifies, policy decides"** and delivered through a staged 5-phase design.

An **Architecture Decision Record** captures a single, significant decision: the context and forces that led to it, the decision itself, and its consequences (positive, negative, and the alternatives weighed). ADRs are immutable once accepted — if a decision changes, a new ADR supersedes the old one rather than editing history. These records are written in the [MADR](https://adr.github.io/madr/) style and are **reverse-documented**: each describes a decision already embodied in the current codebase.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [0001](./0001-fastapi-control-plane-with-isolated-workers.md) | Modular FastAPI Control Plane with Isolated Background Workers | Accepted |
| [0002](./0002-postgresql-for-application-state-and-audit.md) | PostgreSQL for Application State and Audit | Accepted |
| [0003](./0003-neo4j-for-the-dependency-and-architecture-graph.md) | Neo4j for the Dependency and Architecture Graph | Accepted |
| [0004](./0004-deterministic-decision-engine-over-llm-authority.md) | Deterministic Decision Engine over LLM Authority | Accepted |
| [0005](./0005-mockaiprovider-for-deterministic-offline-analysis.md) | MockAIProvider for Deterministic, Offline Analysis | Accepted |
| [0006](./0006-tfidf-historical-evidence-instead-of-pgvector-for-now.md) | TF-IDF Historical Evidence Instead of pgvector (For Now) | Accepted |
| [0007](./0007-defer-kafka-and-kubernetes.md) | Defer Kafka and Kubernetes | Accepted |
| [0008](./0008-sha256-hash-chained-immutable-audit-ledger.md) | SHA-256 Hash-Chained, Append-Oriented Immutable Audit Ledger | Accepted |
| [0009](./0009-five-tier-agent-autonomy-and-governance.md) | Tiered Agent Autonomy and Governance Framework | Accepted |
| [0010](./0010-change-proof-as-the-central-auditable-artifact.md) | Change Proof as the Central Auditable Artifact | Accepted |
