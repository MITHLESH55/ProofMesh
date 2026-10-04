"""
Change Intent Analysis Service.

Derives structured change intent from pull request context, commit messages,
and source code diffs.
"""
from typing import Any, Dict, List, Optional
from app.services.assurance.ai_provider import AIProvider, ProviderFactory
from app.services.assurance.secret_redactor import SecretRedactor


class IntentAnalyzer:
    """Analyzes and structures intent for a given change."""

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self.ai_provider = ai_provider or ProviderFactory.get_provider()

    def analyze_intent(
        self,
        title: str,
        description: str,
        commit_sha: str,
        changed_files: List[str],
        diff_text: str = "",
    ) -> Dict[str, Any]:
        """Derive structured intent from change metadata and sanitized diff."""
        sanitized_diff, _ = SecretRedactor.redact(diff_text)

        context = {
            "title": title,
            "description": description,
            "commit_sha": commit_sha,
            "changed_files": changed_files,
            "diff_text": sanitized_diff,
        }

        # AI proposes intent
        intent_result = self.ai_provider.infer_intent(context)

        # Ensure structured non-null fields
        return {
            "objective": intent_result.get("objective", title or "Unknown objective"),
            "category": intent_result.get("category", "FEATURE"),
            "affected_capability": intent_result.get("affected_capability", "Core System"),
            "expected_behavior": intent_result.get("expected_behavior", ""),
            "affected_components": intent_result.get("affected_components", changed_files),
            "confidence": float(intent_result.get("confidence", 0.9)),
            "model_info": intent_result.get("model_info", {}),
        }
