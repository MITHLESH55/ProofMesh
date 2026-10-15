"""
ProofMesh Demo Enterprise — Inventory Service.

Owns inventory-db. Reserves and releases stock for in-flight orders.
"""
from typing import Dict


class InventoryService:
    """Tracks available stock and reservations per SKU."""

    def __init__(self) -> None:
        self.stock: Dict[str, int] = {}

    def reserve(self, sku: str, quantity: int) -> bool:
        """Reserve stock if available.

        INVARIANT: reserved quantity never exceeds available stock, so the
        on-hand count can never go negative.
        """
        available = self.stock.get(sku, 0)
        if quantity <= 0 or quantity > available:
            return False
        self.stock[sku] = available - quantity
        return True

    def restock(self, sku: str, quantity: int) -> None:
        self.stock[sku] = self.stock.get(sku, 0) + max(0, quantity)
