"""
ProofMesh Demo Enterprise — Seeded Change Scenarios.

Seven controlled software-change scenarios from the ProofMesh master plan, each
expressed as the exact input the deterministic assurance engine consumes
(changed files + unified diff + optional runtime telemetry) together with the
decision band a human reviewer independently expects.

These are NOT generated from ProofMesh output — they are independent ground
truth, mirroring the discipline of the 110-scenario benchmark corpus.

Decision bands: PASS | WARN (review) | BLOCK | RUNTIME_FINDING
Risk levels:    LOW | MEDIUM | HIGH | CRITICAL
"""

# Each scenario is self-contained. `diff_text` uses unified-diff markers
# (leading +/-) so the contract analyzer can distinguish added vs removed code.

SCENARIOS = [
    {
        "id": "DEMO-1-SAFE-REFACTOR",
        "title": "Safe internal refactor of order subtotal helper",
        "category": "safe_change",
        "pdf_reference": "Safe refactor -> expected PASS",
        "narrative": (
            "Extracts subtotal math into a private helper. No public contract, "
            "security surface, or data model is touched, and tests are updated."
        ),
        "changed_files": ["services/order/pricing.py", "tests/order/test_pricing.py"],
        "blast_radius": 1,
        "has_tests_modified": True,
        "diff_text": (
            "--- a/services/order/pricing.py\n"
            "+++ b/services/order/pricing.py\n"
            "@@ def order_total(lines):\n"
            "-    total = sum(l.quantity * l.unit_price_cents for l in lines)\n"
            "-    return total\n"
            "+    return _subtotal_cents(lines)\n"
            "+\n"
            "+\n"
            "+def _subtotal_cents(lines):\n"
            "+    return sum(line.quantity * line.unit_price_cents for line in lines)\n"
        ),
        "expected_decision": "PASS",
        "expected_risk": "LOW",
    },
    {
        "id": "DEMO-2-FORBIDDEN-DB-DEP",
        "title": "Payment service reaches directly into the auth database",
        "category": "architecture_violation",
        "pdf_reference": "Forbidden service-to-database dependency -> BLOCK",
        "narrative": (
            "Payment adds a direct psycopg2 connection to auth-db to look up a "
            "user role, bypassing the auth service API. This violates ownership "
            "boundary policy AUTH-001 (identity data is owned by auth only)."
        ),
        "changed_files": ["services/payment/service.py"],
        "blast_radius": 2,
        "has_tests_modified": False,
        "diff_text": (
            "--- a/services/payment/service.py\n"
            "+++ b/services/payment/service.py\n"
            "@@ class PaymentService:\n"
            "+import psycopg2\n"
            "+\n"
            "+    def _lookup_role(self, user_id):\n"
            "+        conn = psycopg2.connect(\"dbname=auth-db host=auth-db\")\n"
            "+        cur = conn.cursor()\n"
            "+        cur.execute(\"SELECT role FROM users WHERE id = %s\", (user_id,))\n"
            "+        return cur.fetchone()\n"
        ),
        "expected_decision": "BLOCK",
        "expected_risk": "CRITICAL",
    },
    {
        "id": "DEMO-3-TENANT-ISOLATION-REGRESSION",
        "title": "Authorization check relaxed to always return True",
        "category": "authorization_regression",
        "pdf_reference": "Authorization/tenant-isolation regression -> BLOCK",
        "narrative": (
            "A debugging shortcut makes AuthService.authorize() return True "
            "unconditionally, removing the tenant-isolation gate. Breaks the "
            "core security invariant that cross-organization access is denied."
        ),
        "changed_files": ["services/auth/service.py"],
        "blast_radius": 4,
        "has_tests_modified": False,
        "diff_text": (
            "--- a/services/auth/service.py\n"
            "+++ b/services/auth/service.py\n"
            "@@ def authorize(self, user_id, organization_id, permission):\n"
            "         session = self.active_sessions.get(user_id)\n"
            "-        if session.get('organization_id') != organization_id:\n"
            "-            return False\n"
            "+        # TODO: temporarily relaxed while debugging staging\n"
            "+        return True\n"
        ),
        "expected_decision": "BLOCK",
        "expected_risk": "CRITICAL",
    },
    {
        "id": "DEMO-4-BREAKING-API-CONTRACT",
        "title": "Order response schema changed without consumer migration",
        "category": "contract_drift",
        "pdf_reference": "API contract change without consumer update -> REVIEW/HIGH",
        "narrative": (
            "The order API renames the `total` response field to `total_cents`. "
            "Downstream consumers (analytics, notification) are not updated, so "
            "this is a potentially breaking contract drift requiring review."
        ),
        "changed_files": ["services/order/api.py", "services/order/schema.py"],
        "blast_radius": 5,
        "has_tests_modified": False,
        "diff_text": (
            "--- a/services/order/schema.py\n"
            "+++ b/services/order/schema.py\n"
            "@@ class OrderResponse(BaseModel):\n"
            "-    total: int\n"
            "+    total_cents: int\n"
        ),
        "expected_decision": "WARN",
        "expected_risk": "HIGH",
    },
    {
        "id": "DEMO-5-SCHEMA-INCOMPATIBILITY",
        "title": "Relational column type changed with no migration",
        "category": "schema_incompatibility",
        "pdf_reference": "Database schema change without compatibility migration -> HIGH",
        "narrative": (
            "Order.total_cents is changed from int to str directly in the model "
            "with no accompanying Alembic migration. Policy DATA-012 requires a "
            "migration for every relational schema change."
        ),
        "changed_files": ["services/order/models.py"],
        "blast_radius": 6,
        "has_tests_modified": False,
        "diff_text": (
            "--- a/services/order/models.py\n"
            "+++ b/services/order/models.py\n"
            "@@ class Order:\n"
            "-    total_cents: int\n"
            "+    total_cents: str\n"
        ),
        "expected_decision": "WARN",
        "expected_risk": "HIGH",
    },
    {
        "id": "DEMO-6-MISSING-NEGATIVE-TEST",
        "title": "New MFA verification path ships without negative tests",
        "category": "missing_test",
        "pdf_reference": "Missing critical negative test -> REVIEW",
        "narrative": (
            "A multi-factor verification routine is added to the auth subsystem "
            "with no accompanying negative-path tests. A critical security "
            "component changes without regression evidence."
        ),
        "changed_files": ["services/auth/mfa.py"],
        "blast_radius": 2,
        "has_tests_modified": False,
        "diff_text": (
            "--- a/services/auth/mfa.py\n"
            "+++ b/services/auth/mfa.py\n"
            "@@\n"
            "+import hmac\n"
            "+\n"
            "+def verify_mfa(user_id, code):\n"
            "+    expected = _current_totp(user_id)\n"
            "+    return hmac.compare_digest(code, expected)\n"
        ),
        "expected_decision": "WARN",
        "expected_risk": "HIGH",
    },
    {
        "id": "DEMO-7-RUNTIME-REGRESSION",
        "title": "Post-deployment error-rate regression on checkout",
        "category": "runtime_regression",
        "pdf_reference": "Post-deployment latency/error regression -> runtime finding",
        "narrative": (
            "After deploying an approved change, the checkout error rate climbs "
            "from 0.3% to 2.8%. ProofMesh correlates the live telemetry to the "
            "deployment and opens a runtime finding."
        ),
        "changed_files": ["services/order/service.py"],
        "blast_radius": 3,
        "has_tests_modified": True,
        "diff_text": "",
        "telemetry": {
            "reqs": 5000,
            "base_err": 0.3,
            "obs_err": 2.8,
            "base_p95": 110.0,
            "obs_p95": 190.0,
        },
        "expected_decision": "RUNTIME_FINDING",
        "expected_risk": "HIGH",
    },
]

