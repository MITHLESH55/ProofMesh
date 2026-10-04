# ProofMesh — Phase 4: CI/CD & Runtime Assurance

## Overview

Phase 4 of ProofMesh answers the core question:
> **DID THE CHANGE REMAIN SAFE DURING DELIVERY AND AFTER DEPLOYMENT?**

By bridging pre-deployment assurance (Phases 1–3) with post-deployment runtime telemetry, ProofMesh continuously validates software changes from pull request to live production.

```text
GitHub Pull Request
↓
Phase 1 Change Ingestion
↓
Phase 2 Impact Analysis
↓
Phase 3 AI Assurance & Change Proof
↓
Phase 4 CI/CD Policy Gate (CLI / GitHub Status)
↓
Deployment (Staging / Canary / Production)
↓
Runtime Telemetry Ingestion (Prometheus / OpenTelemetry)
↓
Baseline Comparison & Deterministic Regression Detection
↓
Predicted vs Actual Blast Radius Correlation
↓
Extended Change Proof (v2.0.0-phase4)
```

## Core Tenet
# AI PROPOSES. EVIDENCE VERIFIES. POLICY DECIDES.
- Static dependencies predict potential impact.
- Telemetry captures live runtime execution.
- Deterministic rules detect regressions (no AI guesses on metric shifts).
- Policies decide promotion, warning, or blocking.

## Phase 4 Components

1. **CI/CD Assurance Gates**:
   - `POST /api/v1/ci/check` endpoint evaluating gate policies (`PASS`, `WARN`, `BLOCK`, `INSUFFICIENT_EVIDENCE`).
   - `python -m app.cli.check <change_id>` command-line utility with standard exit codes (`0`, `1`, `2`, `3`).
   - GitHub Check Run and Commit Status markdown formatting with direct links to Change Proofs.

2. **Deployment Tracking**:
   - Model `Deployment` with environment tracking (`staging`, `canary`, `production`) and statuses (`NOT_DEPLOYED`, `DEPLOYING`, `DEPLOYED`, `CANARY`, `ROLLED_BACK`, `FAILED`).

3. **Runtime Telemetry & Baselines**:
   - Models `RuntimeBaseline` and `RuntimeObservation`.
   - Prometheus scrape endpoint at `/metrics`.
   - Latency percentiles (p50, p95, p99), error rates, request counts, and HTTP status distributions (2xx/4xx/5xx).

4. **Deterministic Regression Engine**:
   - Compares observed metrics against pre-deployment baselines.
   - Generates structured `RuntimeFinding` records (`ERROR_RATE_REGRESSION`, `PERFORMANCE_REGRESSION`, `AVAILABILITY_REGRESSION`, `RUNTIME_HEALTHY`).

5. **Static Prediction vs Actual Runtime Correlation**:
   - Correlates Phase 2 Neo4j dependency predictions with real microservice traffic.
   - Classifies component traffic states: `MATCH`, `UNEXPECTED_TRAFFIC`, `UNEXPECTED_QUIET`, `REGRESSION`.

6. **Extended Change Proof (v2.0.0-phase4)**:
   - Non-destructive auditable record extending Phase 3 proof with deployment evidence, runtime observations, regression findings, and final combined verdict.

7. **Observability & Frontend**:
   - Docker Compose services for Prometheus (`:9090`) and Grafana (`:3001`).
   - React + TypeScript Runtime Assurance interface with interactive telemetry simulator.
