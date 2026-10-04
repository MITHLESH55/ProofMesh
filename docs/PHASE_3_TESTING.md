# ProofMesh — Phase 3 Testing Strategy & Test Suite Results

## 1. Automated Test Execution

All backend tests are executed using pytest:
```bash
python -m pytest tests
```

Current Results:
```text
======================= 51 passed, 1 warning in 43.73s =======================
```

### Breakdown by Test Suite:
1. **Phase 3 Assurance Services Unit Tests** (`tests/backend/unit/test_assurance_services.py`):
   - `test_intent_analyzer`: Intent inference, categorization, confidence, and provenance metadata.
   - `test_invariant_engine_deterministic_auth_violation`: Catches permissive overrides and flags `VIOLATED`.
   - `test_contract_analyzer_breaking_change`: Catches route deletion and classifies as `BREAKING`.
   - `test_contract_analyzer_additive_change`: Catches added routes and classifies as `COMPATIBLE_CHANGE`.
   - `test_security_analyzer_authorization_bypass`: Flags unconditional authorization returns as `CRITICAL`.
   - `test_test_recommender`: Generates test scaffolds covering invariants and contracts.
   - `test_risk_engine_explainable_factors`: Computes factor-based risk breakdown.
   - `test_policy_engine_blocking_and_insufficient_evidence`: Verifies `BLOCK`, `PASS`, and `INSUFFICIENT_EVIDENCE`.
   - `test_change_proof_builder`: Validates formal Change Proof compilation.

2. **Phase 3 Secret Redactor Unit Tests** (`tests/backend/unit/test_secret_redactor.py`):
   - API keys, GitHub tokens, Bearer tokens, AWS keys, and clean code handling.

3. **Phase 3 REST API Tests** (`tests/backend/api/test_assurance_api.py`):
   - `test_assurance_analyze_endpoint`: End-to-end assurance trigger and response validation.
   - `test_assurance_overview_and_sub_endpoints`: Verifies all sub-resource GET endpoints and policy re-evaluation.

4. **Phase 3 Enterprise Demonstration Scenario** (`tests/e2e/test_demo_scenario.py`):
   - Implements Section 17 scenario: modifying `auth.authorize()` with permissive bypass in `demo-enterprise`, running pipeline, and proving policy `BLOCK`.

5. **Phase 1 & Phase 2 Regression Tests**:
   - All 34 previous unit, API, graph, and primary flow tests continue to pass without regression.

## 2. Frontend Validation

- **Command**: `npm run build` (`tsc && vite build`) in `frontend/`
- **Result**: Zero TypeScript compilation or bundle errors.
- **Note**: ESLint binary is not installed in local `devDependencies`; build and typecheck were verified.
