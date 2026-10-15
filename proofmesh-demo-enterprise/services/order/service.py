"""
ProofMesh Demo Enterprise — Order Service.

Coordinates checkout across inventory (reservation) and payment (charge).
Authorizes every action through the auth service — never by reading auth-db.
"""
from typing import Dict

from services.auth.service import AuthService
from services.order.models import Order


class OrderService:
    """Creates and transitions customer orders within a tenant boundary."""

    def __init__(self, auth: AuthService) -> None:
        self.auth = auth
        self.orders: Dict[str, Order] = {}

    def place_order(self, user_id: str, organization_id: str, order: Order) -> Dict[str, object]:
        """Place an order if the caller is authorized within their organization."""
        if not self.auth.authorize(user_id, organization_id, "order:write"):
            return {"status": 403, "error": "Forbidden"}

        if order.organization_id != organization_id:
            # Defense in depth: never persist a cross-tenant order.
            return {"status": 403, "error": "Tenant mismatch"}

        self.orders[order.id] = order
        return {"status": 201, "order_id": order.id, "total_cents": order.total_cents}
