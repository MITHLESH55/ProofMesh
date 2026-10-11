"""
ProofMesh Demo Enterprise — Payment Service.

Owns payment-db. Charges orders via an external payment gateway abstraction.
Architecture policy AUTH-001 forbids this service from touching auth-db directly;
it must resolve identity/permission questions through the auth service API.
"""
from typing import Dict


class PaymentService:
    """Processes charges and refunds for authorized orders."""

    def __init__(self) -> None:
        self.ledger: Dict[str, Dict[str, object]] = {}

    def charge(self, order_id: str, organization_id: str, amount_cents: int) -> Dict[str, object]:
        """Charge an order. Idempotent on `order_id`.

        INVARIANT: an order is charged at most once; repeated calls return the
        original receipt rather than double-charging.
        """
        if order_id in self.ledger:
            return self.ledger[order_id]

        receipt = {
            "order_id": order_id,
            "organization_id": organization_id,
            "amount_cents": amount_cents,
            "status": "CAPTURED",
        }
        self.ledger[order_id] = receipt
        return receipt
