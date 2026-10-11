# ProofMesh

> **AI-Native Software Change Assurance & Reliability Platform**

[![Phases](https://img.shields.io/badge/Phases_1--5-VERIFIED-success.svg)](docs/PHASE_STATUS.md)
[![Tests](https://img.shields.io/badge/tests-210_passing-success.svg)](#8-running-tests--the-benchmark)
[![Benchmark](https://img.shields.io/badge/benchmark-110_scenarios-blue.svg)](docs/BENCHMARK.md)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-teal.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg)](https://typescriptlang.org)

ProofMesh treats every meaningful software change as an object that must be **proven safe — not merely
reviewed**. It connects evidence from code structure, dependency graphs, architecture policies, security
analysis, tests, CI/CD and runtime telemetry into a single, auditable change-level assurance decision.

**Core principle:** _AI proposes. Evidence verifies. Policy decides._ The LLM layer interprets intent and
proposes invariants and tests, but it never makes the release decision — a deterministic policy engine
does, from verifiable evidence. A missing analysis is reported as **not verified**, never silently as PASS.

---

## 1. The problem

AI-assisted development is increasing software output faster than organizations can verify its
system-wide consequences. A single change can build and pass its own unit tests while silently breaking
downstream services that relied on the old behavior. The bottleneck is shifting from *writing* code to
*verifying, governing and accounting for* it.

ProofMesh is the assurance layer between rapidly changing software and the people and systems responsible
for trusting it. For one pull request it answers:

> **What changed, why, what can it affect, what must remain true, what evidence verifies it, and what
> happened after deployment?**

<!-- APPEND -->

## 2. Architecture

```text
            Developer / AI coding agent
                        |
                 GitHub Pull Request
                        |  (signed webhook, HMAC-SHA256)
                        v
            +-----------------------------+
            |   FastAPI Control Plane      |
            |   REST API + RBAC + audit    |
            +--------------+--------------+
                           |  Redis analysis queue
                           v
                 Analysis Orchestrator
                           |
   +---------+---------+---------+---------+---------+----------+
   |         |         |         |         |         |          |
   v         v         v         v         v         v          v
 Code     Graph     Intent    Security  Contract  Invariant   Test
 (AST)   (Neo4j)   (LLM)     analyzer  analyzer   engine    recommender
   |         |         |         |         |         |          |
   +---------+---------+----+----+---------+---------+----------+
                            v
              Evidence + Explainable Risk Engine
                            v
                Deterministic Policy Engine
                            v
                 PASS  /  REVIEW  /  BLOCK
                            v
             GitHub Check  +  Change Proof (audited)
                            v
          Deployment -> Prometheus / OpenTelemetry
                            v
         Runtime Assurance (regression correlation)
```

- **Control plane:** modular FastAPI service; a Redis-backed background worker runs analysis jobs.
- **Stores:** PostgreSQL (application state, findings, audit), Neo4j (dependency/architecture graph),
  Redis (queue/cache).
- **Staged by design:** Kafka and Kubernetes are deliberately deferred until a measured need exists
  (see [ADR-0007](docs/adr/0007-defer-kafka-and-kubernetes.md)).

## 3. The five phases (all verified)

| Phase | Question it answers | Result | Status |
| :--- | :--- | :--- | :---: |
| **1 — Foundation** | What changed? | Signed GitHub ingestion, tracked change + analysis job, RBAC, audit | ✅ |
| **2 — Code & Graph** | What can it affect? | Python/TS AST extraction, Neo4j dependency graph, impact/blast-radius | ✅ |
| **3 — AI Assurance** | Is it safe, and why? | Intent, invariants, policies, tests, explainable risk, **Change Proof** | ✅ |
| **4 — CI/CD & Runtime** | Did it stay safe in delivery & prod? | PASS/REVIEW/BLOCK gate + CLI, deployment & runtime regression correlation | ✅ |
| **5 — Enterprise & Agents** | Can assurance scale to autonomous orgs? | Multi-repo graph, historical memory, governed agent autonomy, Change Proof v3 | ✅ |

Full detail: [docs/PHASE_STATUS.md](docs/PHASE_STATUS.md).

<!-- APPEND2 -->

## 4. Technology stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, React Router v6 (19 dashboard views).
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic.
- **Persistence & queue:** PostgreSQL 15+, Neo4j 5 (Cypher), Redis 7+.
- **Assurance engine:** deterministic analyzers + a pluggable `AIProvider` abstraction with a
  deterministic offline `MockAIProvider` default (reproducible, $0 to run).
- **CI/CD & runtime:** GitHub Actions gate + CLI, Prometheus `/metrics`, Grafana dashboards.
- **Security:** timing-safe HMAC-SHA256 webhooks, bcrypt, JWT, RBAC (`ADMIN`/`ENGINEER`/`VIEWER`),
  secret redaction before any model call, SHA-256 hash-chained audit ledger.
- **Containerization:** Docker, Docker Compose.

## 5. Measured benchmark results

A controlled corpus of **110 software-change scenarios** with independently authored ground truth is
evaluated against the assurance engine. These are **measured** outcomes (deterministic offline provider),
not targets — full methodology and disclosures in [docs/BENCHMARK.md](docs/BENCHMARK.md).

| Dimension | Measured |
| :--- | :---: |
| Risk detection precision (High/Critical) | **89.1%** |
| Risk detection recall | **79.0%** |
| Architecture violation detection | **98.2%** |
| Impact / blast-radius accuracy | **100.0%** |
| Missing-test detection F1 | **77.8%** |
| Relevant-test suite reduction | **99.1%** |
| Runtime regression detection | **100.0%** |
| Policy decision accuracy | **90.9%** |
| Agent governance enforcement | **100.0%** |
| Historical evidence top-1 recall | **100.0%** |
| Median / p95 analysis latency | **0.023 ms / 0.125 ms** |
| Cost per analyzed change | **$0.00** |

```bash
python benchmark/runner.py          # re-run and regenerate the report
```

## 6. Demo: the simulated enterprise

[`proofmesh-demo-enterprise/`](proofmesh-demo-enterprise/) is a realistic multi-service e-commerce
"company" (gateway, auth, order, payment, inventory, user, notification, analytics, audit) plus **seven
seeded change scenarios** whose correct outcome is known in advance:

```bash
python proofmesh-demo-enterprise/run_scenarios.py -v
```

| Scenario | Expected decision |
| :--- | :--- |
| Safe internal refactor | PASS |
| Payment → auth-db direct access (policy `AUTH-001`) | BLOCK |
| `authorize()` relaxed to `return True` | BLOCK |
| Breaking API response-contract drift | REVIEW |
| Schema change with no migration (`DATA-012`) | REVIEW |
| New MFA path without negative tests | REVIEW |
| Post-deploy error-rate regression | RUNTIME FINDING |

Each outcome is CI-guarded by `tests/e2e/test_demo_enterprise_scenarios.py`.

<!-- APPEND3 -->

## 7. Quickstart (Docker Compose)

```bash
cp .env.example .env
docker compose up --build
```

| Surface | URL |
| :--- | :--- |
| Frontend dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000/api/v1 |
| Interactive Swagger docs | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3002 |

**Seed credentials:** `demo@example.com` / `Password123!` (role `ADMIN`), demo org
*ProofMesh Demo Enterprise*, demo repo `proofmesh-demo-org/demo-enterprise`.

## 8. Running tests & the benchmark

```bash
python -m pytest tests -q                               # backend, integration & E2E suite
cd frontend && npm run build                            # frontend typecheck + production build
python benchmark/runner.py                              # 110-scenario measured benchmark
python proofmesh-demo-enterprise/run_scenarios.py -v    # seeded enterprise demo
```

## 9. REST API surface

74 endpoints across 12 routers under `/api/v1` (full schema at `/docs`):

| Area | Prefix |
| :--- | :--- |
| Authentication & RBAC | `/auth` |
| Repositories | `/repositories` |
| Changes & analysis | `/changes` |
| GitHub webhooks | `/webhooks` |
| Graph & impact analysis | `/graph` |
| AI assurance & Change Proof | `/assurance` |
| CI/CD assurance gates | `/ci` |
| Deployments | `/deployments` |
| Runtime assurance | `/runtime` |
| Enterprise intelligence | `/enterprise` |
| Agent governance & orchestration | `/agents` |
| Health & metrics | `/health`, `/metrics` |

## 10. Repository structure

```text
proofmesh/
├── frontend/                   # React 18 + TypeScript + Vite (19 views)
├── backend/                    # FastAPI control plane + Redis worker
│   ├── app/{api,core,db,models,schemas,repositories,services,workers,cli}
│   └── alembic/                # migrations 001–004 (Phases 1–5)
├── proofmesh-demo-enterprise/  # simulated multi-service enterprise + seeded scenarios
├── benchmark/                  # 110-scenario corpus, runner, metrics, results
├── tests/                      # unit, api, integration, e2e, benchmark
├── infrastructure/             # Dockerfiles, nginx, Prometheus, Grafana
├── docs/                       # architecture, ADRs, API, security, benchmark
└── docker-compose.yml
```

## 11. Documentation

- [Phase status](docs/PHASE_STATUS.md) · [Architecture](docs/ARCHITECTURE.md) ·
  [API reference](docs/API.md) · [Security & threat model](docs/SECURITY.md)
- [Benchmark methodology & results](docs/BENCHMARK.md)
- [Change Proof](docs/CHANGE_PROOF.md) · [CI/CD integration](docs/CI_CD_INTEGRATION.md) ·
  [Runtime assurance](docs/RUNTIME_ASSURANCE.md)
- [Architecture Decision Records](docs/adr/README.md)

## 12. Engineering principles

- Do not make the LLM the final authority; prefer evidence over opaque scores.
- Never confuse *not analyzed* with *safe* — fail safe.
- Introduce distributed infrastructure only when a measured need exists. **Deliberately deferred:**
  Kafka, Kubernetes, external pgvector, and live LLM calls — documented in
  [docs/adr/](docs/adr/README.md), not pretended to be present.
- Measure false positives/negatives on seeded regressions; never invent performance numbers.

---

<sub>ProofMesh — AI-Native Software Change Assurance Platform. Built as a flagship engineering project
spanning backend, system design, AI/ML, software architecture, DevOps and security.</sub>



