"""
Explainable Security Assurance Engine.

Analyzes code diffs and structural symbols for security vulnerabilities,
trust boundary violations, privilege escalation paths, and missing access controls.
"""
from typing import Any, Dict, List, Optional
from app.services.assurance.ai_provider import AIProvider, ProviderFactory
from app.services.assurance.secret_redactor import SecretRedactor


class SecurityAnalyzer:
    """Performs evidence-backed security assurance reviews on code modifications."""

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self.ai_provider = ai_provider or ProviderFactory.get_provider()

    def analyze_security(
        self,
        changed_files: List[str],
        diff_text: str = "",
        impacted_files: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluate code change for security threats backed by concrete evidence."""
        findings: List[Dict[str, Any]] = []

        # 1. Deterministic Rule Matching on Diff
        lower_diff = diff_text.lower()

        # Check for Authorization Bypass / permissive overrides
        if ("def authorize" in lower_diff or "def is_authorized" in lower_diff) and ("return true" in lower_diff or "pass" in lower_diff):
            findings.append({
                "category": "AUTHORIZATION_BYPASS",
                "severity": "CRITICAL",
                "affected_component": next((f for f in changed_files if "auth" in f.lower()), changed_files[0] if changed_files else "auth"),
                "evidence_refs": [f for f in changed_files if "auth" in f.lower()] or changed_files[:1],
                "reasoning": "Detected unconditional permissive authorization return ('return True' or 'pass') bypassing tenant and role checks.",
                "remediation_suggestion": "Restore comprehensive role and organization membership validation before returning True.",
                "confidence": 0.98,
            })

        # Check for Missing Authentication checks on new routes
        if "@router." in lower_diff and "depend" not in lower_diff and ("admin" in lower_diff or "delete" in lower_diff):
            findings.append({
                "category": "MISSING_AUTHENTICATION",
                "severity": "HIGH",
                "affected_component": next((f for f in changed_files if "api" in f.lower()), changed_files[0] if changed_files else "router"),
                "evidence_refs": [f for f in changed_files if "api" in f.lower()] or changed_files[:1],
                "reasoning": "Privileged route handler added without authentication/authorization dependency injection.",
                "remediation_suggestion": "Add `Depends(get_current_user)` or appropriate role permission guard to endpoint declaration.",
                "confidence": 0.90,
            })

        # Check for Insecure Input / raw SQL interpolation
        if "execute(f\"select" in lower_diff or "execute(f\"insert" in lower_diff or "execute(\"select %s\" %" in lower_diff:
            findings.append({
                "category": "INSECURE_INPUT",
                "severity": "CRITICAL",
                "affected_component": changed_files[0] if changed_files else "database",
                "evidence_refs": changed_files[:1],
                "reasoning": "Raw SQL query string interpolation detected. Vulnerable to SQL injection attacks.",
                "remediation_suggestion": "Use SQLAlchemy parameterized queries (`text(\"... :param\"), {\"param\": val}`) instead of f-strings.",
                "confidence": 0.99,
            })

        # Check for Plaintext Secrets
        _, redaction_count = SecretRedactor.redact(diff_text)
        if redaction_count > 0:
            findings.append({
                "category": "SECRET_HANDLING",
                "severity": "HIGH",
                "affected_component": changed_files[0] if changed_files else "configuration",
                "evidence_refs": changed_files[:1],
                "reasoning": f"Detected {redaction_count} potential raw credential or secret pattern(s) embedded in code diff.",
                "remediation_suggestion": "Move credentials to environment variables or secret manager; do not commit secrets.",
                "confidence": 0.92,
            })

        # 2. AI Model Security Evaluation
        sanitized_diff, _ = SecretRedactor.redact(diff_text)
        ai_findings = self.ai_provider.analyze_security({
            "changed_files": changed_files,
            "diff_text": sanitized_diff,
            "impacted_files": impacted_files or [],
        })

        for finding in ai_findings:
            # Deduplicate by category
            if not any(f["category"] == finding.get("category") for f in findings):
                findings.append({
                    "category": finding.get("category", "TRUST_BOUNDARY_VIOLATION"),
                    "severity": finding.get("severity", "MEDIUM"),
                    "affected_component": finding.get("affected_component", changed_files[0] if changed_files else "system"),
                    "evidence_refs": finding.get("evidence_refs", changed_files[:1]),
                    "reasoning": finding.get("reasoning", "Potential security vector identified."),
                    "remediation_suggestion": finding.get("remediation_suggestion", "Review code according to OWASP guidelines."),
                    "confidence": float(finding.get("confidence", 0.85)),
                })

        return findings
