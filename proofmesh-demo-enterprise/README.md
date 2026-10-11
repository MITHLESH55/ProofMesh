# ProofMesh Demo Enterprise

A small but realistic e-commerce "software company" used as the controlled
laboratory for demonstrating ProofMesh end to end. It is the centerpiece of the
project demo: a multi-service codebase plus a set of **seeded change scenarios**
whose correct assurance outcome is known in advance.

> Principle under test: **AI proposes, evidence verifies, policy decides.**

---

## 1. Simulated services

```
                         WEB / MOBILE
                              |
                         API GATEWAY  (edge)
                              |
      +-----------+-----------+-----------+-----------+
      |           |           |           |           |
    AUTH        ORDER      INVENTORY     USER       (platform / domain)
   auth-db    order-db    inventory-db  user-db
      |           |
      |         PAYMENT
      |         payment-db
      +-----------+-----------+
                  |
           MESSAGE BROKER
          /       |        \
  NOTIFICATION  ANALYTICS   AUDIT
                analytics-db audit-db
```

Each service under `services/` is a compact, readable module with real service
logic and explicit invariants in its docstrings (tenant isolation in `auth`,
at-most-once charge in `payment`, append-only hash-chained `audit`, etc.). Data
ownership and allowed dependencies are declared in
[`architecture/policies.yaml`](architecture/policies.yaml).

## 2. Architecture & security policies

`architecture/policies.yaml` is a version-controlled, deterministic policy
manifest the assurance layer enforces regardless of AI output:

| Policy | Type | Severity | Rule |
| --- | --- | --- | --- |
| `AUTH-001` | architecture | critical | No service may touch `auth-db` directly |
| `API-004` | architecture | high | Public admin routes must sit behind auth `Depends(...)` |
| `DATA-007` | security | critical | PII must never be written to the analytics store |
| `DATA-012` | architecture | high | Schema changes must ship with a migration |

## 3. Seeded change scenarios

`demo_scenarios.py` defines seven controlled changes with independently authored
expected outcomes (never derived from ProofMesh output):

| Scenario | Theme | Expected |
| --- | --- | --- |
| `DEMO-1-SAFE-REFACTOR` | Safe internal refactor | PASS / LOW |
| `DEMO-2-FORBIDDEN-DB-DEP` | Payment → auth-db direct access | BLOCK / CRITICAL |
| `DEMO-3-TENANT-ISOLATION-REGRESSION` | `authorize()` returns `True` | BLOCK / CRITICAL |
| `DEMO-4-BREAKING-API-CONTRACT` | Response field renamed, consumers not updated | REVIEW / HIGH |
| `DEMO-5-SCHEMA-INCOMPATIBILITY` | Column type change, no migration | REVIEW / HIGH |
| `DEMO-6-MISSING-NEGATIVE-TEST` | New MFA path, no negative tests | REVIEW / HIGH |
| `DEMO-7-RUNTIME-REGRESSION` | Post-deploy error-rate spike | RUNTIME FINDING / HIGH |

## 4. Running the demo

```bash
# From the repository root
python proofmesh-demo-enterprise/run_scenarios.py       # decision table
python proofmesh-demo-enterprise/run_scenarios.py -v    # full Change Proofs
```

The runner drives each scenario's diff through the **real** assurance engine in
`backend/app/services/assurance/` (security, contract, invariant, risk and
policy analyzers) and layers the architecture policy manifest on top, then prints
a Change-Proof-style decision for each change. It exits non-zero if any scenario
deviates from its expected decision band.

## 5. How it is verified

The scenarios are guarded in CI by
[`tests/e2e/test_demo_enterprise_scenarios.py`](../tests/e2e/test_demo_enterprise_scenarios.py),
so a regression in the engine that changed any demo outcome would fail the test
suite.

```bash
python -m pytest tests/e2e/test_demo_enterprise_scenarios.py -v
```

> No core engine code lives here — this package only composes the platform's
> existing analyzers, exactly as the production orchestrator does.
