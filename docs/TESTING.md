# ProofMesh — Testing Strategy & Execution (Phase 1)

## 1. Overview

Testing in ProofMesh covers all layers of the platform:
- **Unit Tests**: Security utilities, token logic, HMAC verification, Pydantic normalization, worker transitions.
- **API Tests**: Authentication, repositories, change querying, webhook event handling.
- **Integration & E2E Tests**: The complete flow from GitHub webhook receipt to database persistence, worker execution, and API output.

---

## 2. Test Execution Commands

### Running Backend & E2E Tests
```bash
python -m pytest tests -v
```

### Running with Code Coverage
```bash
python -m pytest tests --cov=backend/app -v
```

### Running Frontend Tests & Typecheck
```bash
cd frontend
npm run build
```

---

## 3. Verified Test Matrix

| Test Suite | File | Coverage | Status |
|---|---|---|---|
| Security Unit | `tests/backend/unit/test_security.py` | Password hash/verify, JWT token lifecycle, HMAC validation | **PASSED** |
| Webhook Unit | `tests/backend/unit/test_webhook_service.py` | Webhook verification, payload parsing, error handling | **PASSED** |
| Worker Unit | `tests/backend/unit/test_worker.py` | State transitions (`QUEUED` -> `RUNNING` -> `COMPLETED` / `FAILED`), retries | **PASSED** |
| Auth API | `tests/backend/api/test_auth_api.py` | Register, login, get current user, invalid credentials | **PASSED** |
| Repositories API | `tests/backend/api/test_repositories_api.py` | List repos, get repo, RBAC admin creation, engineer forbidden | **PASSED** |
| Changes API | `tests/backend/api/test_changes_api.py` | Change list, change detail, status check, reanalyze trigger | **PASSED** |
| Webhook API | `tests/backend/api/test_webhooks_api.py` | Valid signature, invalid signature, delivery idempotency, PR synchronize, unsupported event | **PASSED** |
| Health API | `tests/backend/api/test_health_api.py` | `/health` liveness, `/ready` dependency checks | **PASSED** |
| Primary Flow E2E | `tests/e2e/test_primary_flow.py` | Webhook ingestion -> Change persisted -> Analysis queued -> Worker completed -> Dashboard API verification | **PASSED** |
