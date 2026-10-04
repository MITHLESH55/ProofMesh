import pytest
from app.services.assurance.secret_redactor import SecretRedactor


def test_redact_api_keys():
    text = "const apiKey = 'sk-live-1234567890abcdef123456';"
    redacted, count = SecretRedactor.redact(text)
    assert count > 0
    assert "sk-live-1234567890abcdef123456" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_github_tokens():
    text = "git clone https://ghp_abcdefghijklmnopqrstuvwxyz1234567890@github.com/repo"
    redacted, count = SecretRedactor.redact(text)
    assert count > 0
    assert "ghp_" not in redacted
    assert "[REDACTED_GITHUB_TOKEN]" in redacted


def test_redact_bearer_tokens():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDN"
    redacted, count = SecretRedactor.redact(text)
    assert count > 0
    assert "Bearer [REDACTED_TOKEN]" in redacted


def test_redact_aws_keys():
    text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
    redacted, count = SecretRedactor.redact(text)
    assert count > 0
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[REDACTED_AWS_KEY]" in redacted


def test_redact_clean_text():
    text = "def calculate_sum(a: int, b: int) -> int:\n    return a + b\n"
    redacted, count = SecretRedactor.redact(text)
    assert count == 0
    assert redacted == text
