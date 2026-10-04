import hashlib
import hmac
import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    verify_webhook_signature,
)


def test_password_hashing():
    raw_pwd = "SuperSecretPassword123!"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_token_flow():
    user_id = "user-12345"
    token = create_access_token(subject=user_id, extra_claims={"role": "ADMIN"})
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["role"] == "ADMIN"

    # Invalid token check
    assert decode_access_token("invalid.token.payload") is None


def test_webhook_signature_verification():
    secret = "test_webhook_secret_key"
    payload = b'{"action": "opened", "number": 1}'

    # Compute valid signature
    mac = hmac.new(secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256)
    valid_sig = f"sha256={mac.hexdigest()}"

    assert verify_webhook_signature(payload, valid_sig, secret=secret) is True
    assert verify_webhook_signature(payload, "sha256=invalidhexsignature1234", secret=secret) is False
    assert verify_webhook_signature(payload, None, secret=secret) is False
    assert verify_webhook_signature(b'{"different": "body"}', valid_sig, secret=secret) is False
