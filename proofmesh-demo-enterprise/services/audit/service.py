"""
ProofMesh Demo Enterprise — Audit Service.

Supporting service. Appends tamper-evident audit records (append-only, hash
chained) mirroring the platform's own audit ledger design.
"""
import hashlib
from typing import Dict, List, Optional


class AuditService:
    """Append-only, hash-chained audit log."""

    def __init__(self) -> None:
        self.records: List[Dict[str, str]] = []

    def append(self, actor: str, action: str, entity: str) -> str:
        """Append an audit record chained to the previous record's hash."""
        prev_hash = self.records[-1]["hash"] if self.records else "GENESIS"
        payload = f"{prev_hash}|{actor}|{action}|{entity}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.records.append({"actor": actor, "action": action, "entity": entity, "prev": prev_hash, "hash": digest})
        return digest

    def verify_chain(self) -> bool:
        """Recompute the chain to detect tampering."""
        prev_hash = "GENESIS"
        for rec in self.records:
            payload = f"{prev_hash}|{rec['actor']}|{rec['action']}|{rec['entity']}"
            if hashlib.sha256(payload.encode("utf-8")).hexdigest() != rec["hash"]:
                return False
            prev_hash = rec["hash"]
        return True
