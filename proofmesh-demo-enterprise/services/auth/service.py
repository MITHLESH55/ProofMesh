"""
ProofMesh Demo Enterprise — Authentication & Authorization Service.

Owns the identity domain (auth-db). All other services MUST authorize through
this service's API; direct access to auth-db from other services is forbidden
by architecture policy AUTH-001.
"""
from typing import Dict, List, Optional


class AuthService:
    """Enterprise role-based access control and tenant isolation service."""

    def __init__(self) -> None:
        # user_id -> {organization_id, roles, permissions}
        self.active_sessions: Dict[str, Dict[str, object]] = {}

    def authorize(self, user_id: str, organization_id: str, permission: str) -> bool:
        """Verify whether a user holds a permission within a target organization.

        INVARIANT (SECURITY_POLICY_CORE): Unauthorized actors must never receive
        access to resources outside their own organization. Cross-organization
        access must always be rejected before any role check succeeds.
        """
        session = self.active_sessions.get(user_id)
        if not session:
            return False

        # Tenant isolation gate — evaluated BEFORE any role shortcut.
        if session.get("organization_id") != organization_id:
            return False

        roles: List[str] = session.get("roles", [])  # type: ignore[assignment]
        if "ADMIN" in roles:
            return True

        permissions: List[str] = session.get("permissions", [])  # type: ignore[assignment]
        return permission in permissions

    def issue_session(self, user_id: str, organization_id: str, roles: List[str], permissions: List[str]) -> None:
        """Register an authenticated session scoped to a single organization."""
        self.active_sessions[user_id] = {
            "organization_id": organization_id,
            "roles": roles,
            "permissions": permissions,
        }
