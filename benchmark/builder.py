"""
ProofMesh Phase 5 Benchmark Corpus Builder.

Generates 110 deterministic, controlled software-change scenarios across
all 11 ProofMesh assurance dimensions with independently authored ground truth.
"""
import json
import os
from typing import Any, Dict, List, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCENARIOS_DIR = os.path.join(BASE_DIR, "scenarios")
GROUND_TRUTH_DIR = os.path.join(BASE_DIR, "ground_truth")


def build_corpus() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Assemble all 110 scenarios and corresponding ground truths."""
    scenarios: List[Dict[str, Any]] = []
    ground_truths: List[Dict[str, Any]] = []

    # 1. SECURITY VIOLATIONS (SEC-001 to SEC-010)
    sec_data = [
        (
            "SEC-001",
            "SQL Injection via raw f-string interpolation",
            "Direct string formatting into execute() query without parameterization",
            {
                "changed_files": ["app/api/users.py"],
                "diff_text": "- query = db.query(User).filter(User.username == name)\n+ query = db.execute(f\"SELECT * FROM users WHERE username = '{name}'\")",
                "commit_title": "Optimize user query by executing raw SQL string",
                "commit_description": "Direct execution bypasses ORM overhead",
                "has_tests_modified": False,
                "blast_radius": 2,
            },
            {
                "expected_risk_level": "CRITICAL",
                "expected_policy_decision": "BLOCK",
                "is_security_violation": True,
                "expected_security_category": "INSECURE_INPUT",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "BLOCKED",
                "expected_impacted_files_count": 2,
                "relevant_historical_match": "INC-2025-01",
                "rationale": "Raw SQL query string interpolation exposes backend to critical SQL injection attacks.",
            },
        ),
        (
            "SEC-002",
            "Hardcoded JWT Secret Key in configuration",
            "Commits plain-text cryptographic JWT signing secret into config file",
            {
                "changed_files": ["app/core/config.py"],
                "diff_text": "+ JWT_SECRET_KEY = \"super_secret_jwt_signing_key_12345_production\"\n+ ALGORITHM = \"HS256\"",
                "commit_title": "Add default signing key for local and production tokens",
                "commit_description": "Static signing secret simplifies local token generation",
                "has_tests_modified": False,
                "blast_radius": 5,
            },
            {
                "expected_risk_level": "HIGH",
                "expected_policy_decision": "WARN",
                "is_security_violation": True,
                "expected_security_category": "SECRET_HANDLING",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 5,
                "relevant_historical_match": "INC-2024-05",
                "rationale": "Hardcoded JWT secret keys in version control lead to credential leakage.",
            },
        ),
        (
            "SEC-003",
            "Authorization Bypass returning True unconditionally",
            "Replaces tenant role validation with unconditional True return",
            {
                "changed_files": ["app/services/auth/checker.py"],
                "diff_text": "- def authorize(user, role):\n-     return user.role == role and user.is_active\n+ def authorize(user, role):\n+     return True",
                "commit_title": "Bypass authorization check for debugging permissions",
                "commit_description": "Temporary workaround to allow unverified access",
                "has_tests_modified": False,
                "blast_radius": 8,
            },
            {
                "expected_risk_level": "CRITICAL",
                "expected_policy_decision": "BLOCK",
                "is_security_violation": True,
                "expected_security_category": "AUTHORIZATION_BYPASS",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "BLOCKED",
                "expected_impacted_files_count": 8,
                "relevant_historical_match": "INC-2025-33",
                "rationale": "Unconditional return True in authorization function bypasses all RBAC controls.",
            },
        ),
        (
            "SEC-004",
            "Privileged Admin route missing authentication dependency",
            "Adds privileged deletion endpoint without Depends(get_current_user)",
            {
                "changed_files": ["app/api/admin.py"],
                "diff_text": "+ @router.delete(\"/admin/tenants/{tenant_id}\")\n+ def delete_tenant(tenant_id: str):\n+     return {\"deleted\": tenant_id}",
                "commit_title": "Expose tenant deletion admin route",
                "commit_description": "Enables tenant cleanup via administrative endpoint",
                "has_tests_modified": False,
                "blast_radius": 3,
            },
            {
                "expected_risk_level": "HIGH",
                "expected_policy_decision": "WARN",
                "is_security_violation": True,
                "expected_security_category": "MISSING_AUTHENTICATION",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 3,
                "relevant_historical_match": "INC-2025-77",
                "rationale": "Privileged route handler declared without authentication dependencies allows anonymous invocation.",
            },
        ),
        (
            "SEC-005",
            "SQL Injection in Report Exporter query interpolation",
            "Raw SQL f-string query in data export service",
            {
                "changed_files": ["app/services/reports.py"],
                "diff_text": "+ sql = f\"SELECT id, email, role FROM users WHERE org_id = '{org_id}'\"\n+ result = db.execute(f\"SELECT * FROM ({sql})\")",
                "commit_title": "Add direct SQL query for report extraction",
                "commit_description": "Export organization user metrics via raw SQL",
                "has_tests_modified": False,
                "blast_radius": 2,
            },
            {
                "expected_risk_level": "CRITICAL",
                "expected_policy_decision": "BLOCK",
                "is_security_violation": True,
                "expected_security_category": "INSECURE_INPUT",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "BLOCKED",
                "expected_impacted_files_count": 2,
                "relevant_historical_match": "INC-2025-01",
                "rationale": "Direct SQL f-string interpolation in reporting pipeline.",
            },
        ),
        (
            "SEC-006",
            "Hardcoded AWS Secret Access Key in storage driver",
            "Embeds plaintext AWS access keys in driver file",
            {
                "changed_files": ["app/services/storage.py"],
                "diff_text": "+ AWS_ACCESS_KEY_ID = \"AKIAIOSFODNN7EXAMPLE\"\n+ AWS_SECRET_ACCESS_KEY = \"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\"",
                "commit_title": "Configure S3 client credentials",
                "commit_description": "Store static access keys in S3 driver",
                "has_tests_modified": False,
                "blast_radius": 4,
            },
            {
                "expected_risk_level": "HIGH",
                "expected_policy_decision": "WARN",
                "is_security_violation": True,
                "expected_security_category": "SECRET_HANDLING",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 4,
                "relevant_historical_match": "INC-2024-05",
                "rationale": "Hardcoded cloud infrastructure secret keys violate secret storage hygiene.",
            },
        ),
        (
            "SEC-007",
            "Authorization Bypass using pass in is_authorized checker",
            "Replaces permissions check with pass and returns True",
            {
                "changed_files": ["app/services/security/authorizer.py"],
                "diff_text": "- def is_authorized(token, permission):\n-     return validator.verify(token, permission)\n+ def is_authorized(token, permission):\n+     pass\n+     return True",
                "commit_title": "Simplify permission verification routine",
                "commit_description": "Skip token signature verification during integration test",
                "has_tests_modified": False,
                "blast_radius": 6,
            },
            {
                "expected_risk_level": "CRITICAL",
                "expected_policy_decision": "BLOCK",
                "is_security_violation": True,
                "expected_security_category": "AUTHORIZATION_BYPASS",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "BLOCKED",
                "expected_impacted_files_count": 6,
                "relevant_historical_match": "INC-2025-33",
                "rationale": "Permissive authorization check permits unverified identity escalation.",
            },
        ),
        (
            "SEC-008",
            "Privileged Audit Purge endpoint missing authentication",
            "Creates unauthenticated administrative endpoint to delete audit records",
            {
                "changed_files": ["app/api/audit.py"],
                "diff_text": "+ @router.delete(\"/admin/audit_logs/purge\")\n+ def purge_logs():\n+     return {\"purged\": True}",
                "commit_title": "Add purge route for compliance audit log records",
                "commit_description": "Delete audit history upon administrative request",
                "has_tests_modified": False,
                "blast_radius": 2,
            },
            {
                "expected_risk_level": "HIGH",
                "expected_policy_decision": "WARN",
                "is_security_violation": True,
                "expected_security_category": "MISSING_AUTHENTICATION",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 2,
                "relevant_historical_match": "INC-2025-77",
                "rationale": "Unauthenticated audit purge endpoint compromises non-repudiation.",
            },
        ),
        (
            "SEC-009",
            "SQL Injection via string modulo format operator",
            "Uses legacy % string operator to interpolate table name into raw SQL execute",
            {
                "changed_files": ["app/services/maintenance.py"],
                "diff_text": "+ def vacuum_table(name):\n+     db.execute(\"SELECT %s\" % name)",
                "commit_title": "Add table maintenance helper",
                "commit_description": "Execute diagnostic query with modulo string operator",
                "has_tests_modified": False,
                "blast_radius": 1,
            },
            {
                "expected_risk_level": "CRITICAL",
                "expected_policy_decision": "BLOCK",
                "is_security_violation": True,
                "expected_security_category": "INSECURE_INPUT",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "BLOCKED",
                "expected_impacted_files_count": 1,
                "relevant_historical_match": "INC-2025-01",
                "rationale": "Raw SQL formatting with string interpolation operator.",
            },
        ),
        (
            "SEC-010",
            "Hardcoded Database Password in database connection URI",
            "Exposes plaintext postgres credentials in database driver",
            {
                "changed_files": ["app/db/connection.py"],
                "diff_text": "+ DEFAULT_DSN = \"postgresql://dbadmin:P@ssword2026!@postgres-prod:5432/main_db\"",
                "commit_title": "Set fallback DSN for production database",
                "commit_description": "Hardcode default postgres connection URI",
                "has_tests_modified": False,
                "blast_radius": 3,
            },
            {
                "expected_risk_level": "HIGH",
                "expected_policy_decision": "WARN",
                "is_security_violation": True,
                "expected_security_category": "SECRET_HANDLING",
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 3,
                "relevant_historical_match": "INC-2024-05",
                "rationale": "Plaintext database connection password committed to source control.",
            },
        ),
    ]

    for sid, title, desc, inp, exp in sec_data:
        scenarios.append({"id": sid, "title": title, "category": "security_violations", "description": desc, "input": inp})
        ground_truths.append({"id": sid, "category": "security_violations", **exp})

    # 2. RISK CLASSIFICATION (RISK-001 to RISK-010)
    risk_data = [
        (
            "RISK-001",
            "Critical Auth Service Refactoring with Wide Impact",
            "Modifies token verification in auth service affecting 12 downstream components",
            {
                "changed_files": ["app/services/auth/jwt.py"],
                "diff_text": "+ def refresh_token(token):\n+     return jwt.decode(token, verify=False)",
                "commit_title": "Update JWT token decoding routines",
                "commit_description": "Changes token verification and claims extraction",
                "has_tests_modified": False,
                "blast_radius": 12,
            },
            {
                "expected_risk_level": "CRITICAL",
                "expected_policy_decision": "WARN",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 12,
                "relevant_historical_match": None,
                "rationale": "Critical component modified without tests and high blast radius produces CRITICAL risk score.",
            },
        ),
        (
            "RISK-002",
            "Database Schema Migration with Foreign Key Alteration",
            "Modifies relational models affecting multiple persistence entities",
            {
                "changed_files": ["app/models/user.py"],
                "diff_text": "+ organization_id = Column(String, nullable=True)",
                "commit_title": "Relax foreign key constraint on organization",
                "commit_description": "Allow nullable organization identifier in user table",
                "has_tests_modified": False,
                "blast_radius": 8,
            },
            {
                "expected_risk_level": "HIGH",
                "expected_policy_decision": "WARN",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 8,
                "relevant_historical_match": "INC-2025-12",
                "rationale": "Database model modification with moderate blast radius elevates risk score to HIGH.",
            },
        ),
        (
            "RISK-003",
            "Billing Invoice Calculator with Comprehensive Tests",
            "Modifies billing logic with blast radius 6 but accompanied by unit tests",
            {
                "changed_files": ["app/services/billing/invoice.py", "tests/test_invoice.py"],
                "diff_text": "+ def compute_tax(subtotal, rate):\n+     return round(subtotal * rate, 2)",
                "commit_title": "Update invoice tax rounding calculation",
                "commit_description": "Ensure rounding complies with two-decimal accounting standards",
                "has_tests_modified": True,
                "blast_radius": 6,
            },
            {
                "expected_risk_level": "MEDIUM",
                "expected_policy_decision": "PASS",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": False,
                "has_runtime_regression": False,
                "expected_governance_decision": "ALLOWED",
                "expected_impacted_files_count": 6,
                "relevant_historical_match": None,
                "rationale": "Moderate blast radius with verified test coverage results in MEDIUM risk score.",
            },
        ),
        (
            "RISK-004",
            "Date Helper Utility Enhancement with Test Suite",
            "Adds date formatting helpers with 4 dependents and unit tests",
            {
                "changed_files": ["app/utils/date_helper.py", "tests/test_date_helper.py"],
                "diff_text": "+ def format_iso8601(dt):\n+     return dt.isoformat()",
                "commit_title": "Add ISO8601 date formatter helper",
                "commit_description": "Standardize timestamp formatting across utilities",
                "has_tests_modified": True,
                "blast_radius": 4,
            },
            {
                "expected_risk_level": "MEDIUM",
                "expected_policy_decision": "PASS",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": False,
                "has_runtime_regression": False,
                "expected_governance_decision": "ALLOWED",
                "expected_impacted_files_count": 4,
                "relevant_historical_match": None,
                "rationale": "Moderate blast radius with accompanying tests achieves MEDIUM risk.",
            },
        ),
        (
            "RISK-005",
            "API Guide Markdown Documentation Clarification",
            "Documentation only modification with isolated blast radius",
            {
                "changed_files": ["docs/api_guide.md"],
                "diff_text": "+ Note: Ensure Authorization header Bearer token is provided.",
                "commit_title": "Clarify bearer token usage in API guide",
                "commit_description": "Update markdown documentation with authorization instructions",
                "has_tests_modified": False,
                "blast_radius": 1,
            },
            {
                "expected_risk_level": "LOW",
                "expected_policy_decision": "PASS",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": False,
                "has_runtime_regression": False,
                "expected_governance_decision": "ALLOWED",
                "expected_impacted_files_count": 1,
                "relevant_historical_match": None,
                "rationale": "Documentation modifications present negligible operational risk.",
            },
        ),
        (
            "RISK-006",
            "README Markdown Update and Badge Links",
            "Adds build status badges and installation instructions",
            {
                "changed_files": ["README.md"],
                "diff_text": "+ [![Build Status](https://github.com/org/repo/actions/badge.svg)](actions)",
                "commit_title": "Add build status badge to README",
                "commit_description": "Update documentation links and quickstart steps",
                "has_tests_modified": False,
                "blast_radius": 1,
            },
            {
                "expected_risk_level": "LOW",
                "expected_policy_decision": "PASS",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": False,
                "has_runtime_regression": False,
                "expected_governance_decision": "ALLOWED",
                "expected_impacted_files_count": 1,
                "relevant_historical_match": None,
                "rationale": "Non-code documentation edits remain firmly in LOW risk category.",
            },
        ),
        (
            "RISK-007",
            "Authentication Endpoint Route Handler Update",
            "Modifies auth route handler with high blast radius and missing tests",
            {
                "changed_files": ["app/api/auth.py"],
                "diff_text": "+ def issue_token():\n+     return {'token': 'dummy'}",
                "commit_title": "Update auth token controller logic",
                "commit_description": "Modifies authentication token issuance pipeline",
                "has_tests_modified": False,
                "blast_radius": 15,
            },
            {
                "expected_risk_level": "CRITICAL",
                "expected_policy_decision": "WARN",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": True,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 15,
                "relevant_historical_match": None,
                "rationale": "High blast radius across authentication boundary without tests yields CRITICAL risk score.",
            },
        ),
        (
            "RISK-008",
            "Alembic Database Migration Script with Schema Changes",
            "Adds migration script modifying multiple relational constraints",
            {
                "changed_files": ["backend/alembic/versions/004_migration.py"],
                "diff_text": "+ op.alter_column('users', 'email', nullable=True)",
                "commit_title": "Alembic migration to alter user email nullability",
                "commit_description": "Update table columns via migration script",
                "has_tests_modified": True,
                "blast_radius": 12,
            },
            {
                "expected_risk_level": "HIGH",
                "expected_policy_decision": "WARN",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": False,
                "has_runtime_regression": False,
                "expected_governance_decision": "APPROVAL_REQUIRED",
                "expected_impacted_files_count": 12,
                "relevant_historical_match": "INC-2025-12",
                "rationale": "High blast radius database migration carries HIGH risk score.",
            },
        ),
        (
            "RISK-009",
            "Caching Service Redis Adapter with Unit Test",
            "Updates caching adapter with moderate blast radius accompanied by unit tests",
            {
                "changed_files": ["app/services/cache.py", "tests/test_cache.py"],
                "diff_text": "+ def set_cache(k, v):\n+     redis_client.setex(k, 300, v)",
                "commit_title": "Update redis cache expiration timeout",
                "commit_description": "Sets standard 300 second TTL on cached objects",
                "has_tests_modified": True,
                "blast_radius": 5,
            },
            {
                "expected_risk_level": "MEDIUM",
                "expected_policy_decision": "PASS",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": False,
                "has_runtime_regression": False,
                "expected_governance_decision": "ALLOWED",
                "expected_impacted_files_count": 5,
                "relevant_historical_match": None,
                "rationale": "Moderate blast radius with unit tests results in MEDIUM risk score.",
            },
        ),
        (
            "RISK-010",
            "Frontend CSS Design Token Adjustment",
            "Adjusts CSS color variable for dark mode styling",
            {
                "changed_files": ["frontend/src/index.css"],
                "diff_text": "+ --bg-primary: #0a0f1d;",
                "commit_title": "Adjust dark mode primary background token",
                "commit_description": "Refines contrast ratio for dark mode palettes",
                "has_tests_modified": False,
                "blast_radius": 1,
            },
            {
                "expected_risk_level": "LOW",
                "expected_policy_decision": "PASS",
                "is_security_violation": False,
                "expected_security_category": None,
                "has_architecture_violation": False,
                "has_missing_tests": False,
                "has_runtime_regression": False,
                "expected_governance_decision": "ALLOWED",
                "expected_impacted_files_count": 1,
                "relevant_historical_match": None,
                "rationale": "Pure styling CSS token changes without backend dependencies are LOW risk.",
            },
        ),
    ]

    for sid, title, desc, inp, exp in risk_data:
        scenarios.append({"id": sid, "title": title, "category": "risk_classification", "description": desc, "input": inp})
        ground_truths.append({"id": sid, "category": "risk_classification", **exp})

    # 3. DEPENDENCY IMPACT ANALYSIS (DEP-001 to DEP-010)
    dep_data = [
        ("DEP-001", "Isolated API leaf node change", "Modifies health endpoint with 0 downstream dependents", ["app/api/health.py"], 1, "LOW"),
        ("DEP-002", "Shared string formatting helper", "Modifies text formatter imported by 4 downstream modules", ["app/core/formatters.py"], 4, "MEDIUM"),
        ("DEP-003", "Base database entity class", "Modifies base model imported by 14 downstream entity files", ["app/models/base.py"], 14, "HIGH"),
        ("DEP-004", "Authentication token utility", "Modifies token generator imported across 12 services", ["app/core/tokens.py"], 12, "CRITICAL"),
        ("DEP-005", "Email HTML template modification", "Modifies static email template with 1 dependent", ["app/templates/invite.html"], 1, "LOW"),
        ("DEP-006", "Shared HTTP client wrapper", "Modifies HTTP client used by 8 client integration services", ["app/core/http_client.py"], 8, "MEDIUM"),
        ("DEP-007", "Global structured logging engine", "Modifies root logger configuration imported by 15 modules", ["app/core/logging.py"], 15, "HIGH"),
        ("DEP-008", "Standalone diagnostic CLI script", "Modifies diagnostic script with 1 dependent", ["scripts/export_metrics.py"], 1, "LOW"),
        ("DEP-009", "Cache adapter interface", "Modifies cache abstraction with 6 dependent services", ["app/services/cache_adapter.py"], 6, "MEDIUM"),
        ("DEP-010", "Global application settings schema", "Modifies Pydantic settings config imported by 18 modules", ["app/core/config.py"], 18, "HIGH"),
    ]

    for sid, title, desc, files, blast, risk_lvl in dep_data:
        inp = {
            "changed_files": files,
            "diff_text": f"+ # Update {files[0]} logic",
            "commit_title": title,
            "commit_description": desc,
            "has_tests_modified": True,
            "blast_radius": blast,
        }
        exp = {
            "expected_risk_level": risk_lvl,
            "expected_policy_decision": "PASS" if risk_lvl in ["LOW", "MEDIUM"] else "WARN",
            "is_security_violation": False,
            "expected_security_category": None,
            "has_architecture_violation": False,
            "has_missing_tests": False,
            "has_runtime_regression": False,
            "expected_governance_decision": "ALLOWED",
            "expected_impacted_files_count": blast,
            "relevant_historical_match": None,
            "rationale": f"Calculated blast radius is {blast} files based on dependency topology.",
        }
        scenarios.append({"id": sid, "title": title, "category": "dependency_impact_analysis", "description": desc, "input": inp})
        ground_truths.append({"id": sid, "category": "dependency_impact_analysis", **exp})

    # 4. ARCHITECTURE VIOLATIONS (ARCH-001 to ARCH-010)
    arch_data = [
        ("ARCH-001", "Removed GET /api/v1/organizations route", "Breaking route deletion from public REST API", "- @router.get(\"/api/v1/organizations\")", "BREAKING", True, "BLOCK", "CRITICAL"),
        ("ARCH-002", "Removed POST /api/v1/auth/token endpoint", "Breaking deletion of primary authentication route", "- @router.post(\"/api/v1/auth/token\")", "BREAKING", True, "BLOCK", "CRITICAL"),
        ("ARCH-003", "Cascading deletion rule introduced", "Introduces cascade delete behavioral side effect", "+ # delete cascade records from storage", "POTENTIALLY_BREAKING", True, "WARN", "HIGH"),
        ("ARCH-004", "Additive GET /api/v1/health/ping route", "Compatible backwards-compatible route extension", "+ @router.get(\"/api/v1/health/ping\")", "COMPATIBLE_CHANGE", False, "PASS", "LOW"),
        ("ARCH-005", "Additive POST /api/v1/telemetry/events route", "Compatible backwards-compatible telemetry route", "+ @router.post(\"/api/v1/telemetry/events\")", "COMPATIBLE_CHANGE", False, "PASS", "LOW"),
        ("ARCH-006", "Removed DELETE /api/v1/repositories/{id} route", "Breaking route removal from repositories API", "- @router.delete(\"/api/v1/repositories/{id}\")", "BREAKING", True, "BLOCK", "CRITICAL"),
        ("ARCH-007", "Removed PUT /api/v1/users/{id} endpoint", "Breaking route removal breaking mobile client contract", "- @router.put(\"/api/v1/users/{id}\")", "BREAKING", True, "BLOCK", "CRITICAL"),
        ("ARCH-008", "Additive GET /api/v1/agents/metrics route", "Compatible route addition for monitoring agents", "+ @router.get(\"/api/v1/agents/metrics\")", "COMPATIBLE_CHANGE", False, "PASS", "LOW"),
        ("ARCH-009", "Cascading delete on database entity", "Introduces cascading delete in database model", "+ # delete cascade foreign records", "POTENTIALLY_BREAKING", True, "WARN", "HIGH"),
        ("ARCH-010", "Schema definition field modification", "Modifies schema spec with potential contract drift", "+ # schema contract update for records", "POTENTIALLY_BREAKING", True, "WARN", "HIGH"),
    ]

    for sid, title, desc, diff, classif, has_viol, dec, rlvl in arch_data:
        files = ["app/api/routes.py"] if "router" in diff else ["app/models/entities.py"]
        inp = {
            "changed_files": files,
            "diff_text": diff,
            "commit_title": title,
            "commit_description": desc,
            "has_tests_modified": True,
            "blast_radius": 3,
        }
        exp = {
            "expected_risk_level": rlvl,
            "expected_policy_decision": dec,
            "is_security_violation": False,
            "expected_security_category": None,
            "has_architecture_violation": has_viol,
            "has_missing_tests": False,
            "has_runtime_regression": False,
            "expected_governance_decision": "BLOCKED" if dec == "BLOCK" else "ALLOWED",
            "expected_impacted_files_count": 3,
            "relevant_historical_match": "INC-2025-42" if has_viol else None,
            "rationale": f"Contract classification '{classif}' determines architectural violation state ({has_viol}).",
        }
        scenarios.append({"id": sid, "title": title, "category": "architecture_violations", "description": desc, "input": inp})
        ground_truths.append({"id": sid, "category": "architecture_violations", **exp})

    # 5. MISSING TEST DETECTION (TEST-001 to TEST-010)
    test_data = [
        ("TEST-001", "Auth MFA logic modified without test", "app/services/auth/mfa.py", False, 8, True),
        ("TEST-002", "Payment charge computation modified without test", "app/services/billing/charge.py", False, 5, True),
        ("TEST-003", "Password hashing algorithm modified without test", "app/core/security.py", False, 6, True),
        ("TEST-004", "Database migration adding constraints without test", "backend/alembic/versions/migration.py", False, 7, True),
        ("TEST-005", "Auth validator updated with accompanying test", "app/services/auth/validator.py", True, 4, False),
        ("TEST-006", "High blast radius session manager updated without test", "app/services/session.py", False, 9, True),
        ("TEST-007", "Payment refund updated with unit tests", "app/services/billing/refund.py", True, 3, False),
        ("TEST-008", "OAuth token exchange modified without test", "app/services/auth/oauth.py", False, 6, True),
        ("TEST-009", "API webhook dispatcher added with test", "app/api/webhooks.py", True, 2, False),
        ("TEST-010", "Multi-tenant tenant separator updated without test", "app/core/tenant_context.py", False, 8, True),
    ]

    for sid, title, file_path, has_tests, blast, missing_flag in test_data:
        files = [file_path] if not has_tests else [file_path, f"tests/{os.path.basename(file_path)}"]
        inp = {
            "changed_files": files,
            "diff_text": f"+ # Update logic in {file_path}",
            "commit_title": title,
            "commit_description": f"Refactor component {file_path}",
            "has_tests_modified": has_tests,
            "blast_radius": blast,
        }
        exp = {
            "expected_risk_level": "CRITICAL" if ("auth" in file_path or "security" in file_path) and not has_tests else ("HIGH" if not has_tests else "MEDIUM"),
            "expected_policy_decision": "WARN" if missing_flag else "PASS",
            "is_security_violation": False,
            "expected_security_category": None,
            "has_architecture_violation": False,
            "has_missing_tests": missing_flag,
            "has_runtime_regression": False,
            "expected_governance_decision": "APPROVAL_REQUIRED" if missing_flag else "ALLOWED",
            "expected_impacted_files_count": blast,
            "relevant_historical_match": None,
            "rationale": f"High risk or blast radius without tests flags missing_tests={missing_flag}.",
        }
        scenarios.append({"id": sid, "title": title, "category": "missing_test_detection", "description": title, "input": inp})
        ground_truths.append({"id": sid, "category": "missing_test_detection", **exp})

    # 6. SAFE / LOW-RISK CHANGES (SAFE-001 to SAFE-010)
    safe_data = [
        ("SAFE-001", "Fix typos in docstrings", ["app/utils/helpers.py"], "+ \"\"\"Calculate standard moving average.\"\"\""),
        ("SAFE-002", "Update project README guide", ["README.md"], "+ Run `npm run dev` to launch frontend."),
        ("SAFE-003", "Add unit test case to test suite", ["tests/test_helpers.py"], "+ def test_average(): assert avg([2, 4]) == 3"),
        ("SAFE-004", "Update .gitignore for editor artifacts", [".gitignore"], "+ .vscode/\n+ *.swp"),
        ("SAFE-005", "Add explanatory comments to algorithm", ["app/services/math.py"], "+ # Step 1: Normalize vector inputs"),
        ("SAFE-006", "Update copyright header comments", ["app/core/license.py"], "+ # Copyright 2026 ProofMesh Inc."),
        ("SAFE-007", "Add developer setup instructions in docs", ["docs/setup.md"], "+ Install python 3.11 and postgresql."),
        ("SAFE-008", "Update changelog release notes", ["CHANGELOG.md"], "+ ## [v0.5.0] - Phase 5 Enterprise Assurance"),
        ("SAFE-009", "Bump dev linter in package.json", ["frontend/package.json"], "+ \"eslint\": \"^8.57.0\""),
        ("SAFE-010", "Fix grammatical errors in error message string", ["app/core/errors.py"], "+ USER_NOT_FOUND = 'The specified user was not found.'"),
    ]

    for sid, title, files, diff in safe_data:
        inp = {
            "changed_files": files,
            "diff_text": diff,
            "commit_title": title,
            "commit_description": title,
            "has_tests_modified": True if "test" in files[0] else False,
            "blast_radius": 1,
        }
        exp = {
            "expected_risk_level": "LOW",
            "expected_policy_decision": "PASS",
            "is_security_violation": False,
            "expected_security_category": None,
            "has_architecture_violation": False,
            "has_missing_tests": False,
            "has_runtime_regression": False,
            "expected_governance_decision": "ALLOWED",
            "expected_impacted_files_count": 1,
            "relevant_historical_match": None,
            "rationale": "Non-functional, documentation, or trivial formatting changes are deterministically classified as LOW risk.",
        }
        scenarios.append({"id": sid, "title": title, "category": "safe_low_risk_changes", "description": title, "input": inp})
        ground_truths.append({"id": sid, "category": "safe_low_risk_changes", **exp})

    # 7. RUNTIME REGRESSIONS (REG-001 to REG-010)
    reg_data = [
        ("REG-001", "Severe Error Rate Spike to 6.2%", {"base_err": 0.4, "obs_err": 6.2, "base_p95": 100.0, "obs_p95": 115.0, "reqs": 1000, "errs": 62}, True, "CRITICAL", "ERROR_RATE_REGRESSION"),
        ("REG-002", "High Latency Spike to 520ms p95", {"base_err": 0.3, "obs_err": 0.3, "base_p95": 110.0, "obs_p95": 520.0, "reqs": 1000, "errs": 3}, True, "HIGH", "PERFORMANCE_REGRESSION"),
        ("REG-003", "Elevated Error Rate Spike to 3.1%", {"base_err": 0.5, "obs_err": 3.1, "base_p95": 120.0, "obs_p95": 130.0, "reqs": 1000, "errs": 31}, True, "HIGH", "ERROR_RATE_REGRESSION"),
        ("REG-004", "Moderate Latency Spike to 410ms p95", {"base_err": 0.2, "obs_err": 0.2, "base_p95": 120.0, "obs_p95": 410.0, "reqs": 1000, "errs": 2}, True, "HIGH", "PERFORMANCE_REGRESSION"),
        ("REG-005", "Steady Health within Baseline", {"base_err": 0.4, "obs_err": 0.2, "base_p95": 95.0, "obs_p95": 90.0, "reqs": 1000, "errs": 2}, False, "LOW", None),
        ("REG-006", "Steady Health Zero Degradation", {"base_err": 0.3, "obs_err": 0.1, "base_p95": 80.0, "obs_p95": 78.0, "reqs": 1000, "errs": 1}, False, "LOW", None),
        ("REG-007", "Critical Error Rate Spike to 14.5%", {"base_err": 0.5, "obs_err": 14.5, "base_p95": 100.0, "obs_p95": 120.0, "reqs": 1000, "errs": 145}, True, "CRITICAL", "ERROR_RATE_REGRESSION"),
        ("REG-008", "Severe Latency Degradation to 780ms p95", {"base_err": 0.3, "obs_err": 0.3, "base_p95": 100.0, "obs_p95": 780.0, "reqs": 1000, "errs": 3}, True, "HIGH", "PERFORMANCE_REGRESSION"),
        ("REG-009", "Normal Telemetry Jitter within Limits", {"base_err": 0.3, "obs_err": 0.3, "base_p95": 120.0, "obs_p95": 125.0, "reqs": 1000, "errs": 3}, False, "LOW", None),
        ("REG-010", "Zero Telemetry Observations Received", {"base_err": 0.5, "obs_err": 0.0, "base_p95": 120.0, "obs_p95": 0.0, "reqs": 0, "errs": 0}, True, "HIGH", "INSUFFICIENT_RUNTIME_EVIDENCE"),
    ]

    for sid, title, telem, has_reg, rlvl, find_type in reg_data:
        inp = {
            "changed_files": ["app/api/checkout.py"],
            "diff_text": "+ # Deploy runtime changes",
            "commit_title": title,
            "commit_description": title,
            "has_tests_modified": True,
            "blast_radius": 2,
            "telemetry": telem,
        }
        exp = {
            "expected_risk_level": rlvl,
            "expected_policy_decision": "BLOCK" if rlvl == "CRITICAL" else ("WARN" if has_reg else "PASS"),
            "is_security_violation": False,
            "expected_security_category": None,
            "has_architecture_violation": False,
            "has_missing_tests": False,
            "has_runtime_regression": has_reg,
            "expected_governance_decision": "APPROVAL_REQUIRED" if has_reg else "ALLOWED",
            "expected_impacted_files_count": 2,
            "relevant_historical_match": "INC-2025-19" if has_reg else None,
            "rationale": f"Observed telemetry compared against baseline thresholds flags runtime_regression={has_reg}.",
        }
        scenarios.append({"id": sid, "title": title, "category": "runtime_regressions", "description": title, "input": inp})
        ground_truths.append({"id": sid, "category": "runtime_regressions", **exp})

    # 8. POLICY DECISIONS (POL-001 to POL-010)
    pol_data = [
        ("POL-001", "Zero Evidence Provided", [], "", 0, False, None, "INSUFFICIENT_EVIDENCE", "LOW"),
        ("POL-002", "Critical SQL Injection in query", ["app/api/users.py"], "+ db.execute(f\"SELECT * FROM users WHERE name = '{name}'\")", 2, True, "INSECURE_INPUT", "BLOCK", "CRITICAL"),
        ("POL-003", "Breaking API Contract endpoint removal", ["app/api/routes.py"], "- @router.get(\"/api/v1/projects\")", 3, False, None, "BLOCK", "CRITICAL"),
        ("POL-004", "Behavioral Invariant Violation in auth", ["app/services/auth.py"], "- def authorize(): return False\n+ def authorize(): return True", 4, True, "AUTHORIZATION_BYPASS", "BLOCK", "CRITICAL"),
        ("POL-005", "High-severity security finding without criticals", ["app/api/admin.py"], "+ @router.delete(\"/admin/keys\")\n+ def del_keys(): pass", 2, True, "MISSING_AUTHENTICATION", "WARN", "HIGH"),
        ("POL-006", "Potentially breaking schema contract update", ["app/models/records.py"], "+ # delete cascade records", 2, False, None, "WARN", "HIGH"),
        ("POL-007", "Clean documentation change", ["docs/faq.md"], "+ Frequently Asked Questions", 1, False, None, "PASS", "LOW"),
        ("POL-008", "High blast radius change with elevated risk", ["app/models/core.py"], "+ # Update core persistence models", 15, False, None, "WARN", "HIGH"),
        ("POL-009", "Clean bug fix with passing tests", ["app/services/calc.py", "tests/test_calc.py"], "+ return a + b", 2, False, None, "PASS", "LOW"),
        ("POL-010", "Compatible feature extension with complete tests", ["app/api/items.py", "tests/test_items.py"], "+ @router.get(\"/api/v1/items\")", 2, False, None, "PASS", "LOW"),
    ]

    for sid, title, files, diff, blast, is_sec, sec_cat, dec, rlvl in pol_data:
        inp = {
            "changed_files": files,
            "diff_text": diff,
            "commit_title": title,
            "commit_description": title,
            "has_tests_modified": any("test" in f for f in files),
            "blast_radius": blast,
        }
        exp = {
            "expected_risk_level": rlvl,
            "expected_policy_decision": dec,
            "is_security_violation": is_sec,
            "expected_security_category": sec_cat,
            "has_architecture_violation": dec == "BLOCK" and not is_sec,
            "has_missing_tests": False,
            "has_runtime_regression": False,
            "expected_governance_decision": "BLOCKED" if dec == "BLOCK" else ("APPROVAL_REQUIRED" if dec == "WARN" else "ALLOWED"),
            "expected_impacted_files_count": blast,
            "relevant_historical_match": None,
            "rationale": f"Deterministic policy engine rules render decision={dec}.",
        }
        scenarios.append({"id": sid, "title": title, "category": "policy_decisions", "description": title, "input": inp})
        ground_truths.append({"id": sid, "category": "policy_decisions", **exp})

    # 9. MULTI-REPOSITORY ENTERPRISE CHANGES (ENT-001 to ENT-010)
    ent_data = [
        ("ENT-001", "Core Auth Service Change impacting 4 repos", {"source_repo": "auth-service", "downstream": ["user-service", "billing-service", "gateway", "admin-portal"], "is_breaking": True}, "CRITICAL", "BLOCK"),
        ("ENT-002", "Shared Proto Schema package breaking change", {"source_repo": "common-proto", "downstream": ["order-service", "inventory-service"], "is_breaking": True}, "CRITICAL", "BLOCK"),
        ("ENT-003", "Isolated internal service change", {"source_repo": "metrics-agent", "downstream": [], "is_breaking": False}, "LOW", "PASS"),
        ("ENT-004", "Introducing circular cross-repo dependency", {"source_repo": "service-a", "target_repo": "service-b", "has_cycle": True}, "HIGH", "WARN"),
        ("ENT-005", "Payment service change affecting checkout and billing", {"source_repo": "payment-service", "downstream": ["checkout-service", "billing-service"], "is_breaking": False}, "MEDIUM", "PASS"),
        ("ENT-006", "Additive API contract extension consumed by mobile-gateway", {"source_repo": "user-service", "downstream": ["mobile-gateway"], "is_breaking": False}, "LOW", "PASS"),
        ("ENT-007", "Core database schema repository wide update", {"source_repo": "shared-db", "downstream": ["svc-1", "svc-2", "svc-3", "svc-4", "svc-5"], "is_breaking": True}, "CRITICAL", "BLOCK"),
        ("ENT-008", "Telemetry format update in centralized logger", {"source_repo": "logger-sdk", "downstream": ["service-alpha"], "is_breaking": False}, "LOW", "PASS"),
        ("ENT-009", "Service ownership reassigned across enterprise teams", {"source_repo": "catalog-service", "owner_change": True}, "LOW", "PASS"),
        ("ENT-010", "Safe security patch in shared encryption utility", {"source_repo": "crypto-lib", "downstream": ["auth-service", "payment-service"], "is_breaking": False}, "LOW", "PASS"),
    ]

    for sid, title, ent_ctx, rlvl, dec in ent_data:
        inp = {
            "changed_files": [f"{ent_ctx['source_repo']}/src/lib.py"],
            "diff_text": "+ # Enterprise cross-repo change",
            "commit_title": title,
            "commit_description": title,
            "has_tests_modified": True,
            "blast_radius": len(ent_ctx.get("downstream", [])) + 1,
            "enterprise_context": ent_ctx,
        }
        exp = {
            "expected_risk_level": rlvl,
            "expected_policy_decision": dec,
            "is_security_violation": False,
            "expected_security_category": None,
            "has_architecture_violation": ent_ctx.get("is_breaking", False) or ent_ctx.get("has_cycle", False),
            "has_missing_tests": False,
            "has_runtime_regression": False,
            "expected_governance_decision": "BLOCKED" if dec == "BLOCK" else "ALLOWED",
            "expected_impacted_files_count": len(ent_ctx.get("downstream", [])) + 1,
            "relevant_historical_match": None,
            "rationale": f"Enterprise dependency analysis renders verdict={dec} with risk={rlvl}.",
        }
        scenarios.append({"id": sid, "title": title, "category": "multi_repository_enterprise_changes", "description": title, "input": inp})
        ground_truths.append({"id": sid, "category": "multi_repository_enterprise_changes", **exp})

    # 10. AGENT GOVERNANCE / APPROVAL (GOV-001 to GOV-010)
    gov_data = [
        ("GOV-001", "Level 1 Agent attempting PROPOSE_PATCH", {"autonomy_level": 1, "requested_capability": "PROPOSE_PATCH", "requester_id": "agent-1", "approver_id": "human-1", "tokens": 1000, "runtime_s": 10}, "BLOCKED", "Tier allows level 3+"),
        ("GOV-002", "Level 3 Agent requesting MODIFY_PRODUCTION_DB", {"autonomy_level": 3, "requested_capability": "MODIFY_PRODUCTION_DB", "requester_id": "agent-2", "approver_id": "human-1", "tokens": 1000, "runtime_s": 10}, "BLOCKED", "Hard denied capability"),
        ("GOV-003", "Agent attempting self-approval of remediation", {"autonomy_level": 3, "requested_capability": "APPLY_REMEDIATION", "requester_id": "agent-3", "approver_id": "agent-3", "tokens": 1000, "runtime_s": 10}, "BLOCKED", "Self-approval is forbidden"),
        ("GOV-004", "High-risk remediation proposal requiring approval", {"autonomy_level": 3, "requested_capability": "APPLY_REMEDIATION", "requester_id": "agent-4", "approver_id": None, "tokens": 1000, "runtime_s": 10}, "APPROVAL_REQUIRED", "High risk requires signoff"),
        ("GOV-005", "Level 4 Agent performing authorized READ_GRAPH", {"autonomy_level": 4, "requested_capability": "READ_GRAPH", "requester_id": "agent-5", "approver_id": "human-1", "tokens": 1000, "runtime_s": 10}, "ALLOWED", "Authorized within tier"),
        ("GOV-006", "Agent task exceeding token budget limit", {"autonomy_level": 3, "requested_capability": "READ_REPOSITORY", "requester_id": "agent-6", "approver_id": "human-1", "tokens": 650000, "runtime_s": 10}, "BLOCKED", "Exceeds 500,000 tokens"),
        ("GOV-007", "Agent task exceeding execution runtime limit", {"autonomy_level": 3, "requested_capability": "READ_REPOSITORY", "requester_id": "agent-7", "approver_id": "human-1", "tokens": 1000, "runtime_s": 2400}, "BLOCKED", "Exceeds 1800s limit"),
        ("GOV-008", "Prompt injection attempting ESCALATE_PRIVILEGES", {"autonomy_level": 1, "requested_capability": "ESCALATE_PRIVILEGES", "requester_id": "agent-8", "approver_id": "human-1", "tokens": 1000, "runtime_s": 10}, "BLOCKED", "Hard denied capability"),
        ("GOV-009", "Agent attempting cross-tenant resource access", {"autonomy_level": 3, "requested_capability": "READ_REPOSITORY", "requester_id": "agent-9", "approver_id": "human-1", "tokens": 1000, "runtime_s": 10, "tenant_mismatch": True}, "BLOCKED", "Tenant isolation violation"),
        ("GOV-010", "Authorized human approval granted for remediation", {"autonomy_level": 5, "requested_capability": "APPLY_REMEDIATION", "requester_id": "agent-10", "approver_id": "human-admin", "tokens": 1000, "runtime_s": 10}, "ALLOWED", "Authorized human approved"),
    ]

    for sid, title, gov_req, verdict, rat in gov_data:
        inp = {
            "changed_files": ["app/services/agent_worker.py"],
            "diff_text": "+ # Agent task invocation",
            "commit_title": title,
            "commit_description": title,
            "has_tests_modified": True,
            "blast_radius": 1,
            "agent_request": gov_req,
        }
        exp = {
            "expected_risk_level": "CRITICAL" if verdict == "BLOCKED" and "Hard denied" in rat else ("HIGH" if verdict == "APPROVAL_REQUIRED" else "LOW"),
            "expected_policy_decision": "BLOCK" if verdict == "BLOCKED" else ("WARN" if verdict == "APPROVAL_REQUIRED" else "PASS"),
            "is_security_violation": False,
            "expected_security_category": None,
            "has_architecture_violation": False,
            "has_missing_tests": False,
            "has_runtime_regression": False,
            "expected_governance_decision": verdict,
            "expected_impacted_files_count": 1,
            "relevant_historical_match": "INC-2026-02" if "budget" in rat.lower() else None,
            "rationale": rat,
        }
        scenarios.append({"id": sid, "title": title, "category": "agent_governance_approval", "description": title, "input": inp})
        ground_truths.append({"id": sid, "category": "agent_governance_approval", **exp})

    # 11. HISTORICAL EVIDENCE RETRIEVAL (HIST-001 to HIST-010)
    hist_data = [
        ("HIST-001", "SQL injection in authentication query", "SQL injection raw user query bypass", "INC-2025-01"),
        ("HIST-002", "Database connection pool exhaustion leak", "database connection pool exhaustion leak timeout", "INC-2024-88"),
        ("HIST-003", "Breaking API contract in payment webhook", "breaking API contract payment webhook endpoint removed", "INC-2025-42"),
        ("HIST-004", "Canary deployment latency regression p95 spike", "canary deployment latency regression p95 spike degradation", "INC-2025-19"),
        ("HIST-005", "Hardcoded plaintext JWT secret key committed", "hardcoded plaintext JWT secret key credential leak", "INC-2024-05"),
        ("HIST-006", "Cross-tenant authorization boundary data leak", "cross-tenant authorization boundary isolation data leak", "INC-2025-33"),
        ("HIST-007", "Missing database migration table scan index", "missing database migration index full table scan latency", "INC-2025-12"),
        ("HIST-008", "Autonomous agent runaway loop budget exceeded", "autonomous agent runaway loop task token budget exceeded", "INC-2026-02"),
        ("HIST-009", "Unhandled null reference in checkout transaction flow", "unhandled null reference exception checkout order flow", "INC-2024-91"),
        ("HIST-010", "Permissive CORS origin wildcard header vulnerability", "permissive CORS wildcard origin header unauthorized access", "INC-2025-77"),
    ]

    for sid, title, query_text, expected_match in hist_data:
        inp = {
            "changed_files": ["app/services/search.py"],
            "diff_text": "+ # Retrieve historical incident evidence",
            "commit_title": title,
            "commit_description": title,
            "has_tests_modified": True,
            "blast_radius": 1,
            "historical_query": {"query": query_text},
        }
        exp = {
            "expected_risk_level": "HIGH",
            "expected_policy_decision": "WARN",
            "is_security_violation": False,
            "expected_security_category": None,
            "has_architecture_violation": False,
            "has_missing_tests": False,
            "has_runtime_regression": False,
            "expected_governance_decision": "APPROVAL_REQUIRED",
            "expected_impacted_files_count": 1,
            "relevant_historical_match": expected_match,
            "rationale": f"Semantic query matches historical incident {expected_match}.",
        }
        scenarios.append({"id": sid, "title": title, "category": "historical_evidence_retrieval", "description": title, "input": inp})
        ground_truths.append({"id": sid, "category": "historical_evidence_retrieval", **exp})

    return scenarios, ground_truths


def write_benchmark_files():
    """Write individual scenario and ground-truth JSON files."""
    scenarios, ground_truths = build_corpus()

    os.makedirs(SCENARIOS_DIR, exist_ok=True)
    os.makedirs(GROUND_TRUTH_DIR, exist_ok=True)

    # Validate before writing
    if len(scenarios) < 100:
        raise ValueError(f"Scenario count ({len(scenarios)}) must be at least 100!")

    seen_ids = set()
    for s in scenarios:
        sid = s["id"]
        if sid in seen_ids:
            raise ValueError(f"Duplicate scenario ID found: {sid}")
        seen_ids.add(sid)

    for s in scenarios:
        sid = s["id"]
        path = os.path.join(SCENARIOS_DIR, f"{sid}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)

    for gt in ground_truths:
        sid = gt["id"]
        # Validate required fields
        required_fields = [
            "id", "category", "expected_risk_level", "expected_policy_decision",
            "is_security_violation", "has_architecture_violation",
            "has_missing_tests", "has_runtime_regression", "rationale",
        ]
        for field in required_fields:
            if field not in gt:
                raise ValueError(f"Missing required ground truth field '{field}' in {sid}")

        path = os.path.join(GROUND_TRUTH_DIR, f"{sid}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(gt, f, indent=2)

    print(f"Successfully generated {len(scenarios)} scenarios and {len(ground_truths)} ground-truth files.")


if __name__ == "__main__":
    write_benchmark_files()
