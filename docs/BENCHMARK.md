# ProofMesh Benchmark Methodology & Measured Results

ProofMesh is evaluated against a controlled corpus of **110 software-change scenarios** with
independently authored ground truth, spanning all 11 assurance dimensions. This document describes the
methodology and records the latest **measured** results. Numbers are produced by running the engine —
they are not targets, and per the project's non-negotiable principles no performance figure is invented.

Reproduce:

```bash
python benchmark/runner.py            # regenerates benchmark/results/*
python -m pytest tests/benchmark -v   # validates the framework & metrics
```

---

## 1. Design & integrity

- **Independent ground truth.** Each scenario in `benchmark/scenarios/` has a matching label in
  `benchmark/ground_truth/`. Labels are authored independently and are **never** derived from ProofMesh
  output.
- **Fail-fast validation.** The runner (`benchmark/runner.py`) refuses to run if there are duplicate IDs,
  missing required ground-truth fields, fewer than 100 scenarios, or any scenario/ground-truth ID
  mismatch.
- **Deterministic engine.** Scenarios are evaluated through the real assurance analyzers backed by the
  offline `MockAIProvider`, so results are fully reproducible and cost $0.

## 2. Dimensions (10 scenarios each)

Security violations · risk classification · dependency/impact analysis · architecture violations ·
missing-test detection · safe/low-risk changes · runtime regressions · policy decisions ·
multi-repository/enterprise changes · agent governance & approvals · historical evidence retrieval.

## 3. Measured accuracy & quality

| Dimension | Metric | Measured |
| :--- | :--- | :---: |
| Risk detection | Precision (High/Critical) | 89.1% |
| Risk detection | Recall (High/Critical) | 79.0% |
| Risk detection | F1 | 83.8% |
| Risk classification | Exact 4-tier match | 69.1% |
| Architecture | Contract/boundary drift detection | 98.2% |
| Impact analysis | Blast-radius proximity | 100.0% |
| Missing-test | Precision / Recall / F1 | 87.5% / 70.0% / 77.8% |
| Test selection | Relevant-test suite reduction | 99.1% |
| Runtime | Regression detection accuracy | 100.0% |
| Policy | Deterministic verdict match | 90.9% |
| Agent governance | Capability & budget enforcement | 100.0% |
| Historical evidence | TF cosine top-1 recall | 100.0% |

## 4. Latency & cost

| Metric | Measured |
| :--- | :---: |
| Median (p50) scenario latency | ~0.02 ms |
| p95 scenario latency | ~0.12 ms |
| Monetary cost per analyzed change | $0.00 |

## 5. Honest disclosures

- **$0.00 cost / no GPU:** analysis runs as in-process CPU heuristics, AST parsing and pure-Python TF
  cosine math under the deterministic offline provider — no external LLM API calls are dispatched.
- **Recall gaps are real and reported, not hidden.** Risk recall (79.0%) and exact 4-tier classification
  (69.1%) are the weakest dimensions; they are published as-is. A conservative engine that under-escalates
  some medium cases is preferred to one that fabricates confidence.
- **External vector-DB indexing** metrics are not applicable: similarity is computed in memory
  ([ADR-0006](adr/0006-tfidf-historical-evidence-instead-of-pgvector-for-now.md)).

The full machine-readable payload and generated report live in
[`benchmark/results/`](../benchmark/results/) and are regenerated on every `benchmark/runner.py` run.
