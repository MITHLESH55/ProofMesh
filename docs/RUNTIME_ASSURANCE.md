# Runtime Assurance Guide

## Philosophy & Core Rules

1. **Observe First. Infer Second. Never Invent.**
   - All runtime claims must stem directly from recorded `RuntimeObservation` records.
   - Missing telemetry is never treated as success; it is explicitly reported as `INSUFFICIENT_RUNTIME_EVIDENCE`.

2. **Deterministic Regression Thresholds**
   - ProofMesh does not use non-deterministic heuristics to evaluate metrics.
   - Deterministic rules evaluated:
     - **Error Rate Spike**: `observed_error_rate > (baseline_error_rate * 2.5)` OR `observed_error_rate > 2.0%` -> `ERROR_RATE_REGRESSION`
     - **Latency Degradation**: `observed_p95_latency > (baseline_p95_latency * 1.75)` OR `observed_p95_latency > 350ms` -> `PERFORMANCE_REGRESSION`
     - **5xx Server Errors**: `rate_5xx > 1.0%` -> `AVAILABILITY_REGRESSION`
     - **Healthy Verification**: All metrics within baseline envelope -> `RUNTIME_HEALTHY`

3. **Predicted vs Observed Discrepancy Matrix**
   - ProofMesh correlates static code graph blast radius (from Phase 2 Neo4j graph) with runtime telemetry:
     - Predicted impacted + active healthy traffic -> `MATCH`
     - Predicted impacted + no traffic -> `UNEXPECTED_QUIET`
     - Unpredicted component + active traffic -> `UNEXPECTED_TRAFFIC`
     - Active regression -> `REGRESSION`

4. **Extended Change Proof (v2.0.0-phase4)**
   - The original Phase 3 Change Proof remains immutably preserved.
   - The Phase 4 Extended Change Proof links:
     - Change metadata & PR
     - Pre-deployment decision & risk level
     - Target deployment environment, commit SHA, timestamp
     - Post-deployment runtime observation metrics
     - Structured findings & regression evidence
     - Final combined verdict (`VERIFIED_SAFE_IN_RUNTIME`, `RUNTIME_REGRESSION_DETECTED`, `DEPLOYED_WITH_RUNTIME_WARNINGS`, `BLOCKED_PRE_DEPLOYMENT`).
