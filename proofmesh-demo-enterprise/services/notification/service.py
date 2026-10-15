"""
ProofMesh Demo Enterprise — Notification Service.

Supporting service. Consumes order/payment events from the message broker and
delivers transactional notifications. Holds no database of its own.
"""
from typing import Dict, List


class NotificationService:
    """Delivers transactional notifications for domain events."""

    def __init__(self) -> None:
        self.outbox: List[Dict[str, str]] = []

    def notify(self, user_id: str, channel: str, template: str) -> None:
        """Queue a notification. Payload carries references, not PII."""
        self.outbox.append({"user_id": user_id, "channel": channel, "template": template})
