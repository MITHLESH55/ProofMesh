"""
ProofMesh Demo Enterprise — Authentication & Authorization Service.
"""
from typing import Dict, List, Optional


class AuthService:
    """Enterprise role-based access control and tenant isolation service."""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, str]] = {}

    def authorize(self, user_id: str, organization_id: str, permission: str) -> bool:
        """Verify whether user has required permission in the target organization.
        
        INVARIANT: Unauthorized users must never receive access to resources outside their organization.
        """
        session = self.active_sessions.get(user_id)
        if not session:
            return False

        if session.get("organization_id") != organization_id:
            return False

        user_roles = session.get("roles", [])
        if "ADMIN" in user_roles:
            return True

        return permission in session.get("permissions", [])
