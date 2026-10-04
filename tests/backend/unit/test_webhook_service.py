import hashlib
import hmac
import json
import pytest
from app.core.errors import WebhookError
from app.services.github.webhook_service import GitHubWebhookService


def generate_signature(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def test_webhook_service_valid_payload():
    secret = "my_secret"
    payload_dict = {
        "action": "opened",
        "number": 42,
        "repository": {
            "id": 123456,
            "name": "demo-repo",
            "full_name": "org/demo-repo",
            "owner": {"login": "org", "id": 1},
            "default_branch": "main",
        },
        "pull_request": {
            "id": 98765,
            "number": 42,
            "title": "Add feature X",
            "body": "PR description",
            "user": {"login": "developer", "id": 2},
            "head": {"sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"},
            "base": {"sha": "0000000000000000000000000000000000000000"},
            "state": "open",
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = generate_signature(raw_body, secret)

    event_type, parsed = GitHubWebhookService.verify_and_parse(
        raw_body=raw_body,
        signature_header=sig,
        event_type_header="pull_request",
        webhook_secret=secret,
    )

    assert event_type == "pull_request"
    assert parsed.action == "opened"
    assert parsed.pull_request.number == 42
    assert parsed.pull_request.head.sha == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"


def test_webhook_service_invalid_signature():
    raw_body = b'{"action": "opened"}'
    with pytest.raises(WebhookError) as exc_info:
        GitHubWebhookService.verify_and_parse(
            raw_body=raw_body,
            signature_header="sha256=invalid",
            event_type_header="pull_request",
            webhook_secret="secret",
        )
    assert exc_info.value.code == "INVALID_WEBHOOK_SIGNATURE"


def test_webhook_service_missing_event_header():
    raw_body = b'{"action": "opened"}'
    sig = generate_signature(raw_body, "secret")
    with pytest.raises(WebhookError) as exc_info:
        GitHubWebhookService.verify_and_parse(
            raw_body=raw_body,
            signature_header=sig,
            event_type_header=None,
            webhook_secret="secret",
        )
    assert exc_info.value.code == "MISSING_EVENT_HEADER"
