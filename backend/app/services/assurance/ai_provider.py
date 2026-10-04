"""
AI Model Provider Abstraction.

Provides pluggable AI model providers for Phase 3 assurance analysis,
enforcing secret redaction, confidence scoring, provenance tracking, and
deterministic offline testing via MockAIProvider.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.assurance.secret_redactor import SecretRedactor


class AIProvider(ABC):
    """Abstract base class for AI model providers."""

    def __init__(self, model_name: str, version: str):
        self.model_name = model_name
        self.version = version

    @abstractmethod
    def infer_intent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Infer structured change intent from diff and commit metadata."""
        pass

    @abstractmethod
    def propose_invariants(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Propose behavioral invariants that should hold across the change."""
        pass

    @abstractmethod
    def analyze_security(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate code diff for security concerns and vulnerability vectors."""
        pass

    @abstractmethod
    def recommend_tests(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate candidate test recommendations for modified components."""
        pass


class MockAIProvider(AIProvider):
    """Deterministic, offline AI provider used for unit testing and local assurance analysis."""

    def __init__(self, model_name: str = "proofmesh-mock-ai", version: str = "3.0.0"):
        super().__init__(model_name=model_name, version=version)

    def infer_intent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        title = context.get("title", "")
        description = context.get("description", "")
        changed_files = context.get("changed_files", [])
        diff_text = context.get("diff_text", "")

        # Sanitize diff
        sanitized_diff, _ = SecretRedactor.redact(diff_text)

        # Categorize change based on diff & metadata signals
        category = "FEATURE"
        lower_title = (title + " " + description).lower()
        if "fix" in lower_title or "bug" in lower_title or "patch" in lower_title:
            category = "BUG_FIX"
        elif "refactor" in lower_title or "clean" in lower_title:
            category = "REFACTOR"
        elif "security" in lower_title or "auth" in lower_title:
            category = "SECURITY"
        elif "perf" in lower_title or "optimize" in lower_title:
            category = "PERFORMANCE"
        elif any("test" in f for f in changed_files):
            category = "TEST_ONLY" if all("test" in f for f in changed_files) else "FEATURE"

        objective = title if title else f"Update {len(changed_files)} files across repository"
        affected_capability = "Authentication & Access Control" if "auth" in lower_title else "Core Services"

        latency_ms = round((time.time() - start) * 1000, 2)
        return {
            "objective": objective,
            "category": category,
            "affected_capability": affected_capability,
            "expected_behavior": f"Modifies behavior of {', '.join(changed_files[:3])} to implement '{objective}'",
            "affected_components": changed_files,
            "confidence": 0.92,
            "model_info": {
                "provider": "MockAIProvider",
                "model": self.model_name,
                "version": self.version,
                "prompt_version": "v1.0.0",
                "latency_ms": latency_ms,
            },
        }

    def propose_invariants(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        changed_files = context.get("changed_files", [])
        diff_text = context.get("diff_text", "").lower()
        invariants = []

        if any("auth" in f.lower() for f in changed_files) or "authorize" in diff_text or "token" in diff_text:
            invariants.append({
                "invariant_type": "AI_PROPOSED",
                "description": "Unauthorized users must not receive access to protected multi-tenant organizational resources.",
                "affected_component": "auth_service",
                "source": "AI_INTENT_REASONING",
                "evidence_refs": [f for f in changed_files if "auth" in f.lower()],
                "confidence": 0.95,
                "verification_status": "VERIFIED" if "permission" in diff_text or "role" in diff_text else "UNVERIFIED",
            })

        if any("user" in f.lower() or "org" in f.lower() for f in changed_files):
            invariants.append({
                "invariant_type": "AI_PROPOSED",
                "description": "Cross-tenant boundaries must remain strictly isolated during resource queries.",
                "affected_component": "data_access_layer",
                "source": "TENANT_ISOLATION_RULE",
                "evidence_refs": changed_files[:2],
                "confidence": 0.90,
                "verification_status": "VERIFIED",
            })

        return invariants

    def analyze_security(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        changed_files = context.get("changed_files", [])
        diff_text = context.get("diff_text", "")
        findings = []

        # Check for potential auth bypasses in diff
        if "authorize" in diff_text.lower() and ("return true" in diff_text.lower() or "pass" in diff_text.lower()):
            findings.append({
                "category": "AUTHORIZATION_BYPASS",
                "severity": "CRITICAL",
                "affected_component": "auth.py",
                "evidence_refs": [f for f in changed_files if "auth" in f.lower()],
                "reasoning": "Detected explicit permissive override in authorization checking function.",
                "remediation_suggestion": "Ensure strict role and organization membership validation is enforced.",
                "confidence": 0.96,
            })
        elif "secret" in diff_text.lower() and ("hardcoded" in diff_text.lower() or "password123" in diff_text.lower()):
            findings.append({
                "category": "SECRET_HANDLING",
                "severity": "HIGH",
                "affected_component": changed_files[0] if changed_files else "config",
                "evidence_refs": changed_files[:1],
                "reasoning": "Detected plain text secret keyword assignment in modified code.",
                "remediation_suggestion": "Extract credentials to environment variables or secret store.",
                "confidence": 0.88,
            })

        return findings

    def recommend_tests(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        changed_files = context.get("changed_files", [])
        title = context.get("title", "code change")
        recommendations = []

        for f in changed_files:
            component_name = f.split("/")[-1].replace(".py", "").replace(".ts", "")
            recommendations.append({
                "target_component": f,
                "test_title": f"test_{component_name}_contract_integrity",
                "test_code_scaffold": f"def test_{component_name}_contract_integrity():\n    # Test behavior under valid and unauthorized conditions\n    pass\n",
                "reason": f"Verifies behavior and boundary conditions introduced in {title}",
                "invariant_covered": "Contract Compatibility",
                "expected_behavior": f"Ensure {component_name} behaves deterministically for edge cases",
                "confidence": 0.88,
            })

        return recommendations


class ProviderFactory:
    """Factory creating configured AI providers."""

    @staticmethod
    def get_provider() -> AIProvider:
        # Defaults to MockAIProvider for reliable offline verification and tests
        return MockAIProvider()
