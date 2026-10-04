"""
Secret & Credential Redaction Service.

Ensures no private keys, passwords, API tokens, or secrets are leaked to AI
model providers or stored unredacted in assurance evidence.
"""
import re
from typing import Tuple

SECRET_PATTERNS = [
    # API Keys & Tokens
    (re.compile(r'(?i)(api[_-]?key|apikey|secret|token|password|passwd|auth[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{8,})["\']?'), r'\1: "[REDACTED]"'),
    # GitHub Tokens
    (re.compile(r'gh[pousr]_[A-Za-z0-9_]{36,255}'), '[REDACTED_GITHUB_TOKEN]'),
    # Generic Bearer Tokens
    (re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{16,}'), 'Bearer [REDACTED_TOKEN]'),
    # AWS Access Keys
    (re.compile(r'(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}'), '[REDACTED_AWS_KEY]'),
    # Private Keys
    (re.compile(r'-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----[\s\S]+?-----END[ A-Z0-9_-]+PRIVATE KEY-----'), '[REDACTED_PRIVATE_KEY]'),
    # Generic Hex / High Entropy Secrets (32+ hex chars preceded by key keyword)
    (re.compile(r'(?i)(secret|credential|private|signature)\s*[:=]\s*[0-9a-fA-F]{32,}'), r'\1: [REDACTED_HEX_SECRET]'),
]


class SecretRedactor:
    """Sanitizes text and diffs by masking secrets before AI processing."""

    @staticmethod
    def redact(text: str) -> Tuple[str, int]:
        """Redact secrets from the input text.

        Returns:
            Tuple of (sanitized_text, count_of_redactions)
        """
        if not text:
            return "", 0

        sanitized = text
        total_redactions = 0

        for pattern, replacement in SECRET_PATTERNS:
            new_text, count = pattern.subn(replacement, sanitized)
            if count > 0:
                total_redactions += count
                sanitized = new_text

        return sanitized, total_redactions
