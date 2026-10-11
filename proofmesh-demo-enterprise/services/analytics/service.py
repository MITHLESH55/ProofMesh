"""
ProofMesh Demo Enterprise — Analytics Service.

Supporting service. Aggregates business metrics into analytics-db.

POLICY DATA-007 (security, critical): PII (email, full_name, phone_number, ssn)
must NEVER be written to the analytics store. Only anonymized identifiers and
aggregated counts are permitted.
"""
from typing import Dict


class AnalyticsService:
    """Records anonymized, aggregated business events."""

    def __init__(self) -> None:
        self.events: Dict[str, int] = {}

    def record_event(self, event_name: str, anonymized_org_hash: str) -> None:
        """Increment an aggregate counter keyed by event + anonymized tenant."""
        key = f"{event_name}:{anonymized_org_hash}"
        self.events[key] = self.events.get(key, 0) + 1
