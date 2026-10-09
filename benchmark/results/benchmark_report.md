# ProofMesh Phase 5 Controlled Benchmark Report

**Benchmark Execution Date**: 2026-10-07 19:06:47Z  
**Total Scenarios Evaluated**: 110  
**Assurance Engine Architecture**: Deterministic Offline AI Provider (`MockAIProvider`)  
**Status**: **BENCHMARK COMPLETE & VERIFIED**

---

## 1. Executive Summary

A deterministic, controlled benchmark corpus of **110 software-change scenarios** was executed against the ProofMesh Phase 5 assurance engine. Every scenario includes independently authored ground-truth labels spanning all 11 assurance dimensions. All metrics below represent measured empirical outcomes.

---

## 2. Category Distribution

| Assurance Dimension | Scenario Count |
| :--- | :---: |
| `agent_governance_approval` | 10 |
| `architecture_violations` | 10 |
| `dependency_impact_analysis` | 10 |
| `historical_evidence_retrieval` | 10 |
| `missing_test_detection` | 10 |
| `multi_repository_enterprise_changes` | 10 |
| `policy_decisions` | 10 |
| `risk_classification` | 10 |
| `runtime_regressions` | 10 |
| `safe_low_risk_changes` | 10 |
| `security_violations` | 10 |
| **Total Scenarios** | **110** |

---

## 3. Measured Accuracy & Quality Metrics

| Evaluation Dimension | Metric | Measured Value | Target / Benchmark |
| :--- | :--- | :---: | :---: |
| **Risk Detection Precision** | Precision (High/Critical) | **89.1%** | > 85.0% |
| **Risk Detection Recall** | Recall (High/Critical) | **79.0%** | > 90.0% |
| **Risk F1 Score** | Harmonic Mean | **83.8%** | > 88.0% |
| **Risk Classification Accuracy** | Exact Category Match (4-tier) | **69.1%** | > 85.0% |
| **Architecture Detection Accuracy** | Contract / Boundary Drift | **98.2%** | > 90.0% |
| **Impact Analysis Proximity Accuracy** | Blast Radius Proximity | **100.0%** | > 85.0% |
| **Missing-Test Detection Precision** | Precision on Untested Paths | **87.5%** | > 85.0% |
| **Missing-Test Detection Recall** | Recall on Untested Paths | **70.0%** | > 90.0% |
| **Missing-Test Detection F1** | Harmonic Mean | **77.8%** | > 88.0% |
| **Relevant Test Suite Reduction** | Test Scope Reduction | **99.1%** | > 80.0% |
| **Runtime Regression Detection** | Overall Accuracy | **100.0%** | > 95.0% |
| **Policy Decision Accuracy** | Deterministic Verdict Match | **90.9%** | > 90.0% |
| **Agent Governance Accuracy** | Capability & Budget Enforcement | **100.0%** | > 95.0% |
| **Historical Evidence Retrieval** | TF-IDF Top-1 Recall | **100.0%** | > 90.0% |

---

## 4. Latency & Performance Profile

Analysis latency was measured using high-resolution monotonic clocks (`time.perf_counter()`) for each individual scenario:

| Latency Metric | Measured Duration | Target SLA |
| :--- | :---: | :---: |
| **Minimum Scenario Latency** | `0.010 ms` | < 10.0 ms |
| **Mean Scenario Latency** | `0.036 ms` | < 25.0 ms |
| **Median (p50) Scenario Latency** | `0.024 ms` | < 20.0 ms |
| **95th Percentile (p95) Latency** | `0.122 ms` | < 50.0 ms |
| **Maximum Scenario Latency** | `0.253 ms` | < 100.0 ms |

---

## 5. Cost Accounting & Honest Disclosures

### Objectively Measured Metrics:
- **Monetary Cost Per Change**: **$0.00 USD**
- **Average Simulated Tokens Analyzed**: **153.0 tokens / scenario**

### Unavailable Metrics & Technical Rationale:
1. **Commercial LLM API Invoiced Cost**: ProofMesh runs with a deterministic offline heuristic model (`MockAIProvider`). Because no external OpenAI/Anthropic/Google Cloud API calls are dispatched, live cloud billing does not occur ($0.00 incurred).
2. **GPU Memory Footprint / VRAM Bandwidth**: ProofMesh assurance is executed via in-process CPU heuristic rules, AST parsers, and TF-IDF matrix math. GPU acceleration is not required.
3. **External Vector DB Indexing Time**: Vector similarity is computed in-memory via pure-Python TF-IDF cosine similarity. External pgvector indexing benchmarks are not applicable to the current architecture.
