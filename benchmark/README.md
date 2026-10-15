# ProofMesh Phase 5 Controlled Benchmark Suite

Comprehensive, deterministic benchmark suite evaluating the ProofMesh Assurance Engine across 11 core software assurance dimensions.

---

## 1. Directory Structure

```text
benchmark/
├── scenarios/                  # 110 deterministic software-change scenario specifications
│   ├── SEC-001.json ... SEC-010.json
│   ├── RISK-001.json ... RISK-010.json
│   ├── DEP-001.json ... DEP-010.json
│   ├── ARCH-001.json ... ARCH-010.json
│   ├── TEST-001.json ... TEST-010.json
│   ├── SAFE-001.json ... SAFE-010.json
│   ├── REG-001.json ... REG-010.json
│   ├── POL-001.json ... POL-010.json
│   ├── ENT-001.json ... ENT-010.json
│   ├── GOV-001.json ... GOV-010.json
│   └── HIST-001.json ... HIST-010.json
├── ground_truth/               # 110 independently authored human ground-truth labels
│   ├── SEC-001.json ... HIST-010.json
├── runner.py                   # Benchmark execution engine, runner CLI & validator
├── metrics.py                  # Objective metric calculation engine
├── builder.py                  # Corpus generator and validation utility
├── results/                    # Machine-readable and human-readable evaluation outputs
│   ├── benchmark_results.json  # Raw evaluation and metric JSON payload
│   └── benchmark_report.md     # Detailed markdown report
└── README.md                   # Benchmark suite documentation
```

---

## 2. Assurance Dimensions Covered (110 Scenarios)

The benchmark corpus contains **110 controlled scenarios** (10 per category) covering every operational dimension of ProofMesh:

1. **Security Violations (`SEC-001` - `SEC-010`)**: Raw SQL injection via f-strings and format operators, hardcoded JWT secrets, hardcoded AWS credentials, authorization bypass returns, unauthenticated administrative endpoints, and hardcoded database connection passwords.
2. **Risk Classification (`RISK-001` - `RISK-010`)**: 4-tier risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) evaluating component criticality (authentication, database persistence), blast radius, and test coverage signals.
3. **Dependency / Impact Analysis (`DEP-001` - `DEP-010`)**: Isolated leaf node changes (blast radius 1), first-order module dependents, high blast-radius base models, shared HTTP clients, and global configuration settings.
4. **Architecture Violations (`ARCH-001` - `ARCH-010`)**: Semantic contract analysis detecting breaking route removals (e.g. `DELETE /api/v1/repositories/{id}`), cascading delete behavioral drifts, and compatible additive extensions.
5. **Missing-Test Detection (`TEST-001` - `TEST-010`)**: Detection of untested high-risk code paths (MFA, billing charges, password hashing, database migrations, OAuth exchanges) versus adequately tested changes.
6. **Safe / Low-Risk Changes (`SAFE-001` - `SAFE-010`)**: Docstring typo fixes, README quickstart guides, developer setup instructions, `.gitignore` entries, and documentation badge updates.
7. **Runtime Regressions (`REG-001` - `REG-010`)**: Pre-deployment baseline versus live telemetry comparison detecting error rate spikes (e.g., 0.4% to 6.2%), p95 latency degradation (e.g., 110ms to 520ms), and telemetry absence.
8. **Policy Decisions (`POL-001` - `POL-010`)**: Deterministic policy evaluation rendering `PASS`, `WARN`, `BLOCK`, or `INSUFFICIENT_EVIDENCE` based on explicit evidence records.
9. **Multi-Repository / Enterprise Changes (`ENT-001` - `ENT-010`)**: Enterprise dependency graph evaluations detecting cross-repo blast radiuses, shared proto schema breaking changes, and cyclic microservice dependencies.
10. **Agent Governance & Approvals (`GOV-001` - `GOV-010`)**: Autonomy tier capability bounds (levels 0-5), hard-denied actions (`MODIFY_PRODUCTION_DB`), self-approval blocking, token budget limits, runtime timeouts, and prompt injection mitigation.
11. **Historical Evidence Retrieval (`HIST-001` - `HIST-010`)**: Semantic search using pure-Python TF-IDF cosine similarity to recall historical change proofs and incident records.

---

## 3. Ground Truth Independence & Integrity

To preserve scientific rigor:
- **Independent Authorship**: Ground truth labels are maintained independently and **NEVER** generated from ProofMesh predictions.
- **Fail-Fast Validation**:
  - Duplicate scenario or ground-truth IDs immediately halt execution with `ValueError`.
  - Missing required fields (`id`, `category`, `expected_risk_level`, `expected_policy_decision`, `is_security_violation`, `has_architecture_violation`, `has_missing_tests`, `has_runtime_regression`, `rationale`) fail validation.
  - Scenario counts below 100 fail validation immediately.
  - Mismatched scenario and ground-truth ID sets fail validation.

---

## 4. Execution & Usage

### Running the Benchmark
```bash
# Run full benchmark with verbose scenario logging
python benchmark/runner.py -v

# Run with custom output paths
python benchmark/runner.py --output-json benchmark/results/custom.json --output-report benchmark/results/custom.md
```

### Running Benchmark Framework Tests
```bash
# Run automated benchmark framework and metric validation tests
python -m pytest tests/benchmark -v
```

---

## 5. Metric Definitions

- **Risk Precision**: $\frac{TP}{TP + FP}$ for detecting elevated (High/Critical) risks.
- **Risk Recall**: $\frac{TP}{TP + FN}$ for detecting elevated (High/Critical) risks.
- **Classification Accuracy**: Exact 4-tier match rate (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **Architecture Detection Accuracy**: Match rate for breaking contract / architectural boundary flags.
- **Impact Analysis Proximity Accuracy**: Accuracy of dependency blast-radius evaluation.
- **Missing-Test F1 Score**: Harmonic mean of precision and recall for detecting missing test suites on critical code modifications.
- **Relevant Test Suite Reduction**: Percentage reduction in test execution scope achieved by executing targeted recommended tests instead of the full 187-test backend suite.
- **Runtime Regression Accuracy**: Detection accuracy of post-deployment error rate and latency anomalies against pre-deployment baselines.
- **Analysis Latencies (p50, p95)**: Per-scenario execution latency captured via high-resolution monotonic clock (`time.perf_counter()`).
- **Monetary Cost**: Documented as **$0.00** per analyzed change due to deterministic offline heuristic execution.
