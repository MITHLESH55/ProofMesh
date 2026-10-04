# ProofMesh — Phase 3 Specification: AI Assurance & Explainable Risk

## 1. Objective

Phase 3 introduces the AI Assurance & Explainable Risk layer to ProofMesh. Building upon Phase 1 change ingestion and Phase 2 code and dependency intelligence, Phase 3 addresses the fundamental engineering question:

> **IS THE CHANGE SAFE, AND WHY?**

Phase 3 operates under the core foundational principle:
# AI PROPOSES. EVIDENCE VERIFIES. POLICY DECIDES.

---

## 2. Key Capabilities Implemented

### 2.1 Change Intent Analysis
- **Service**: `backend/app/services/assurance/intent_analyzer.py`
- Extracts structured intent from PR title, description, commit metadata, and sanitized diff.
- Classifies changes into discrete categories: `FEATURE`, `BUG_FIX`, `REFACTOR`, `PERFORMANCE`, `SECURITY`, `CONFIGURATION`, `DATABASE`, `API`, `DEPENDENCY`, `TEST_ONLY`, `UNKNOWN`.
- Tracks provenance: provider, model name, version, prompt version, confidence, and latency.

### 2.2 Behavioral Invariant Engine
- **Service**: `backend/app/services/assurance/invariant_engine.py`
- Integrates deterministic invariants with AI-proposed behavioral hypotheses:
  - **DETERMINISTIC**: Invariants verified via concrete rules (e.g. auth checks on protected routes, tenant isolation constraints, relational foreign key preservation).
  - **AI_PROPOSED**: Hypotheses proposed based on semantic reasoning.
- Explicit verification statuses: `VERIFIED`, `VIOLATED`, `UNVERIFIED`.

### 2.3 Semantic Contract Analysis
- **Service**: `backend/app/services/assurance/contract_analyzer.py`
- Detects API endpoint modifications, route additions, route deletions, and parameter drift.
- Classifies contract stability:
  - `NO_CHANGE`: Implementation modified without public interface drift.
  - `COMPATIBLE_CHANGE`: Additive routes or optional parameters.
  - `POTENTIALLY_BREAKING`: Cascading behavior changes or schema updates.
  - `BREAKING`: Route deletion or mandatory field additions without migration.

### 2.4 Security Assurance Engine
- **Service**: `backend/app/services/assurance/security_analyzer.py`
- Evidence-backed security evaluations for:
  - `AUTHORIZATION_BYPASS`: Unconditional permissive returns (`return True`, `pass`).
  - `MISSING_AUTHENTICATION`: Privileged endpoints without auth dependency injection.
  - `INSECURE_INPUT`: String-interpolated SQL statements vulnerable to injection.
  - `SECRET_HANDLING`: Embedded passwords, tokens, or private keys.
- Assigns severity: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` with actionable remediation guidance.

### 2.5 Explainable Risk Engine
- **Service**: `backend/app/services/assurance/risk_engine.py`
- Replaces arbitrary black-box risk numbers with transparent, factor-based composite risk scoring (0.0 to 100.0).
- Explicit contributing factors:
  - Subsystem criticality (Authentication, Authorization, Database).
  - Structural blast radius (traversed from Phase 2 Neo4j dependency graph).
  - Security finding severity.
  - Contract drift classification.
  - Invariant violation status.
  - Test coverage gaps.
- Maps to standard risk tiers: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

### 2.6 AI-Assisted Test Recommendations
- **Service**: `backend/app/services/assurance/test_recommender.py`
- Generates targeted candidate tests and test scaffolds covering modified logic, invariants, and contract changes.
- Safe execution boundary: tests are proposed as reviewable scaffolds without arbitrary code execution.

### 2.7 Unified Traceable Evidence Ledger
- **Model**: `EvidenceRecord`
- Every assurance conclusion traces back to concrete evidence units (`CODE_DIFF`, `AST_FACT`, `GRAPH_RELATION`, `IMPACT_PATH`, `API_CONTRACT`, `INVARIANT`, `SECURITY_FINDING`).
- Unsupported AI claims are marked as low-confidence or unverified.

### 2.8 Deterministic Policy Decision Engine
- **Service**: `backend/app/services/assurance/policy_engine.py`
- Evaluates assembled evidence against strict governance rules:
  - `BLOCK`: Critical security finding, invariant violation, breaking API contract.
  - `WARN`: High risk score, high-severity security finding, or potentially breaking drift.
  - `INSUFFICIENT_EVIDENCE`: Absence of verifiable diff, graph relations, or facts.
  - `PASS`: All required invariants verified, zero critical issues, and stable contracts.

### 2.9 Formal Change Proof Artifact
- **Service**: `backend/app/services/assurance/change_proof_builder.py`
- Assembles a structured, auditable artifact addressing all 10 core verification questions:
  1. What Changed?
  2. Why Did It Change?
  3. What Can It Affect?
  4. What Behavior May Change?
  5. What Contracts May Change?
  6. What Security Properties Are Affected?
  7. What Tests Cover It?
  8. What Evidence Supports the Conclusion?
  9. What Remains Uncertain?
  10. What Policy Decision Was Made?

---

## 3. Database Schema & Migration

- Migration: `backend/alembic/versions/002_phase3_assurance_schema.py`
- Tables created:
  - `change_intents`
  - `behavioral_invariants`
  - `semantic_contracts`
  - `security_findings`
  - `test_recommendations`
  - `risk_assessments`
  - `evidence_records`
  - `policy_decisions`
  - `change_proofs`

---

## 4. REST API Surface

Registered under `/api/v1/assurance`:
- `POST /api/v1/assurance/analyze/{change_id}`: Triggers assurance evaluation.
- `GET /api/v1/assurance/{analysis_run_id}`: Retrieves full overview dossier.
- `GET /api/v1/assurance/{analysis_run_id}/intent`: Returns change intent.
- `GET /api/v1/assurance/{analysis_run_id}/invariants`: Returns invariants and statuses.
- `GET /api/v1/assurance/{analysis_run_id}/contracts`: Returns semantic contract drift.
- `GET /api/v1/assurance/{analysis_run_id}/security`: Returns explainable security findings.
- `GET /api/v1/assurance/{analysis_run_id}/risk`: Returns explainable risk score & factors.
- `GET /api/v1/assurance/{analysis_run_id}/evidence`: Returns the evidence ledger.
- `GET /api/v1/assurance/{analysis_run_id}/proof`: Returns the formal Change Proof.
- `POST /api/v1/assurance/{analysis_run_id}/decision`: Re-evaluates governance policy.

---

## 5. UI Implementation

- **Location**: `frontend/src/pages/AssuranceView.tsx` (routed at `/assurance/:id`).
- Features:
  - Change Proof interactive collapsible reader.
  - Risk factor breakdown cards with point weights.
  - Evidence explorer tracing findings to source references.
  - Governance policy rule verification inspector.
  - Integration with Analysis Runs in `ChangeDetail.tsx`.
