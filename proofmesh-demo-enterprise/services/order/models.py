"""
ProofMesh Demo Enterprise — Order Service domain models.

Owns order-db. Schema changes here must ship with a migration (policy DATA-012)
because downstream services (payment, analytics, audit) read these records.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class OrderLine:
    sku: str
    quantity: int
    unit_price_cents: int


@dataclass
class Order:
    """A customer order. `organization_id` scopes the record to one tenant."""

    id: str
    organization_id: str
    user_id: str
    lines: List[OrderLine] = field(default_factory=list)
    status: str = "PENDING"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_cents(self) -> int:
        return sum(line.quantity * line.unit_price_cents for line in self.lines)
