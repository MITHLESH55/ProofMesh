# Phase 4 Architecture — CI/CD & Runtime Assurance

## Architecture Diagram

```mermaid
graph TD
    PR[GitHub Pull Request] --> P1[Phase 1 Ingestion & Webhook]
    P1 --> P2[Phase 2 Impact Analysis & Neo4j Graph]
    P2 --> P3[Phase 3 AI Assurance & Change Proof]
    P3 --> CI_GATE[Phase 4 CI/CD Gate & CLI check]
    
    CI_GATE -->|PASS / WARN| DEP[Deployment Engine / Target Environment]
    CI_GATE -->|BLOCK| BLK[CI Check Fails / PR Blocked]
    
    DEP --> OTEL[Runtime Telemetry / OpenTelemetry & Prometheus]
    OTEL --> SCRAPE[ProofMesh /metrics Scraper]
    
    SCRAPE --> OBS_STORE[(PostgreSQL: runtime_observations & baselines)]
    P2 --> PRED_MATCHER[Prediction Matcher]
    OBS_STORE --> PRED_MATCHER
    
    OBS_STORE --> REG_ENG[Deterministic Runtime Assurance Engine]
    REG_ENG --> FINDINGS[(runtime_findings)]
    
    FINDINGS --> EXT_PROOF[Extended Change Proof v2.0.0]
    PRED_MATCHER --> EXT_PROOF
    P3 --> EXT_PROOF
    
    EXT_PROOF --> GRAFANA[Grafana Dashboard :3001]
    EXT_PROOF --> UI[ProofMesh Web UI /runtime]
```

## Data Models

### 1. `deployments`
- `id`: UUID
- `repository_id`: Foreign key to `repositories.id`
- `change_id`: Foreign key to `changes.id`
- `analysis_run_id`: Foreign key to `analysis_runs.id`
- `commit_sha`: Git commit hash
- `environment`: `staging` | `production` | `canary`
- `status`: `NOT_DEPLOYED` | `DEPLOYING` | `DEPLOYED` | `CANARY` | `ROLLED_BACK` | `FAILED`
- `deployed_at`, `created_at`

### 2. `runtime_baselines`
- `id`: UUID
- `deployment_id`: Foreign key to `deployments.id`
- `service_name`: Name of service
- `endpoint`: HTTP endpoint path or wildcard
- `request_rate`, `error_rate`, `p50_latency_ms`, `p95_latency_ms`, `p99_latency_ms`
- `sample_window_seconds`: Baseline window duration

### 3. `runtime_observations`
- `id`: UUID
- `deployment_id`: Foreign key to `deployments.id`
- `service_name`, `endpoint`
- `request_count`, `error_count`, `error_rate`
- `p50_latency_ms`, `p95_latency_ms`, `p99_latency_ms`
- `status_2xx_count`, `status_4xx_count`, `status_5xx_count`
- `observed_at`

### 4. `runtime_findings`
- `id`: UUID
- `deployment_id`: Foreign key to `deployments.id`
- `finding_type`: `RUNTIME_HEALTHY` | `RUNTIME_REGRESSION` | `PERFORMANCE_REGRESSION` | `ERROR_RATE_REGRESSION` | `AVAILABILITY_REGRESSION` | `INSUFFICIENT_RUNTIME_EVIDENCE`
- `severity`: `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`
- `service_name`, `endpoint_or_metric`
- `baseline_value`, `observed_value`, `threshold_value`
- `evidence`: Human-readable and machine-auditable narrative
- `confidence`: Confidence score (0.0 - 1.0)

### 5. `ci_assurance_checks`
- `id`: UUID
- `change_id`: Foreign key to `changes.id`
- `commit_sha`: String
- `gate_decision`: `PASS` | `WARN` | `BLOCK` | `INSUFFICIENT_EVIDENCE`
- `policy_summary`: JSON
- `exit_code`: Integer
- `github_check_id`: Optional external check run identifier
- `created_at`
