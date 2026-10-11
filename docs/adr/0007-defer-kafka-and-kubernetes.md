# ADR 0007: Defer Kafka and Kubernetes

- Status: Accepted
- Date: 2026-10-11

## Context
ProofMesh is an assurance platform whose value is correctness of its evidence-and-policy pipeline, not operational scale. A standing project principle is to "introduce distributed infrastructure only when a measured need exists." Event-streaming (Kafka) and container orchestration (Kubernetes) are frequently added reflexively to portfolio projects, adding large operational and cognitive cost without a demonstrated throughput, decoupling, or multi-node requirement.

## Decision
Deliberately defer both Kafka and Kubernetes. Asynchronous work is handled by a Redis queue consumed by an isolated worker (see ADR 0001), and the entire system — PostgreSQL, Redis, Neo4j, backend API, worker, frontend, and the Prometheus/Grafana observability stack — is composed and run via a single `docker-compose.yml`. Both technologies are recorded as future options to be adopted only against a concrete, measured need.

## Consequences
### Positive
- Dramatically lower operational complexity: the whole platform starts with one `docker compose up`.
- Keeps the demo self-contained and reproducible for reviewers, with no cluster or broker to provision.
- Engineering effort stays focused on assurance correctness rather than infra plumbing.
### Negative / Trade-offs
- Redis-queue delivery and Compose-based scaling are less robust than Kafka durability or Kubernetes self-healing/autoscaling under high load.
- A later migration to streaming/orchestration will require real integration work rather than being pre-wired.
- Single-host Compose has no built-in multi-node failover.
### Alternatives considered
- Adopt Kafka now: rejected; no measured event-streaming/throughput need, and it adds brokers, topics, and schema management overhead.
- Adopt Kubernetes now: rejected; no multi-node scaling or self-healing requirement at current scope; Compose is sufficient.
- Serverless/managed queue (SQS, etc.): rejected; introduces cloud coupling and breaks the self-contained local demo.
