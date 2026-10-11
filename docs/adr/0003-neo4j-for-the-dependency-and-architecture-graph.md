# ADR 0003: Neo4j for the Dependency and Architecture Graph

- Status: Accepted
- Date: 2026-10-11

## Context
A core ProofMesh evidence source is "what can this change affect?" — the blast radius. Answering it requires traversing software structure relationships (files, classes, functions/methods, imports) to arbitrary depth and computing transitive impact. These recursive, variable-depth traversals are expensive and clumsy in relational SQL, but map naturally onto a property graph. This underpins the IMPACT_ANALYSIS stage of the pipeline.

## Decision
Model the code dependency and architecture graph in Neo4j, accessed via Cypher through `backend/app/services/graph/` (`graph_service.py`, `neo4j_connection.py`). Parsed source structures are ingested as `File`, `Class`, and `Function` nodes with `BELONGS_TO`, `DEFINES`, `HAS_METHOD`, and `IMPORTS` relationships, and impact/blast-radius queries use variable-length path traversal (e.g., `-[:IMPORTS*1..N]->`).

## Consequences
### Positive
- Variable-depth traversal (direct and transitive dependents) is expressed concisely and runs efficiently.
- Blast-radius and subgraph-visualization queries are first-class rather than recursive-CTE workarounds.
- `MERGE`-based ingestion makes graph updates idempotent across re-analysis of the same commit.
- The graph layer is isolated behind a service, and the worker degrades gracefully when Neo4j is unavailable (the graph step is skipped, not fatal).
### Negative / Trade-offs
- A second datastore adds operational surface (backup, auth, availability) beyond PostgreSQL.
- Keeping the graph consistent with the relational system of record requires deliberate ingestion steps.
- Import resolution is heuristic (path guessing by extension), so edges can be approximate for unresolved/new files.
### Alternatives considered
- Recursive SQL (CTEs) in PostgreSQL: rejected; deep transitive traversal is slow and hard to maintain.
- In-memory graph (NetworkX) rebuilt per request: rejected; not persistent and does not scale across workers/requests.
- A single polyglot store: rejected; no relational store matches native graph traversal performance for this access pattern.
