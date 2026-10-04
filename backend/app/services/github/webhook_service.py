import json
from typing import Any, Dict, Optional, Tuple
from app.core.errors import WebhookError
from app.core.security import verify_webhook_signature
from app.schemas.webhook import GitHubWebhookPayload


class GitHubWebhookService:
    SUPPORTED_ACTIONS = {"opened", "synchronize", "reopened", "closed"}

    @staticmethod
    def verify_and_parse(
        raw_body: bytes,
        signature_header: Optional[str],
        event_type_header: Optional[str],
        webhook_secret: Optional[str] = None,
    ) -> Tuple[str, GitHubWebhookPayload]:
        # 1. Verify HMAC-SHA256 signature
        if not signature_header or not verify_webhook_signature(raw_body, signature_header, secret=webhook_secret):
            raise WebhookError("Invalid or missing webhook signature", code="INVALID_WEBHOOK_SIGNATURE")

        # 2. Verify GitHub event type
        if not event_type_header:
            raise WebhookError("Missing X-GitHub-Event header", code="MISSING_EVENT_HEADER")

        # 3. Parse JSON payload
        try:
            payload_dict = json.loads(raw_body.decode("utf-8"))
            payload = GitHubWebhookPayload.model_validate(payload_dict)
        except Exception as exc:
            raise WebhookError(f"Malformed webhook payload: {str(exc)}", code="MALFORMED_WEBHOOK_PAYLOAD")

        return event_type_header, payload
