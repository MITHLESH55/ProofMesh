# ADR 0006: TF-IDF Historical Evidence Instead of pgvector (For Now)

- Status: Accepted
- Date: 2026-10-11

## Context
Phase 5 adds historical engineering memory: past change proofs, incidents, and remediations should be retrievable by semantic similarity so the system can learn from prior outcomes. A full vector-search stack (pgvector or an external embedding service) would add infrastructure, model dependencies, and operational cost — before there is a measured need or a corpus large enough to justify it. The demo must stay self-contained and reproducible.

## Decision
Implement semantic retrieval as a lightweight, dependency-free, pure-Python term-frequency cosine-similarity search in `backend/app/services/enterprise/historical_evidence_service.py`. Documents and queries are tokenized (stop-word filtered), vectorized with augmented/log-normalized term frequency, and ranked by cosine similarity. The code and docstrings explicitly document pgvector / an external embedding service as the production upgrade path.

## Consequences
### Positive
- Zero new infrastructure or dependencies; retrieval runs entirely in-process and offline.
- Deterministic and reproducible results, consistent with the benchmark philosophy.
- A clean, documented seam (`search`, `_compute_tfidf_vector`, `_cosine_similarity`) to swap in pgvector/embeddings later.
### Negative / Trade-offs
- The current vectorizer uses term frequency only; true inverse-document-frequency (IDF) weighting across the corpus is noted as a future refinement, so rare-term discrimination is weaker than full TF-IDF.
- Lexical (bag-of-words) similarity cannot capture true semantic/synonym relationships the way learned embeddings can.
- Scoring every candidate in Python does not scale to large corpora (no ANN index).
### Alternatives considered
- pgvector extension: rejected for now; adds infra and a migration/ops burden before a measured need (deferred, not discarded).
- External embedding API (OpenAI/Cohere): rejected; introduces cost, network dependency, and non-determinism in the demo.
- Full-text search (Postgres `tsvector`): rejected; ties retrieval to the relational store and still lacks semantic ranking, with little gain over the in-process approach at this scale.
