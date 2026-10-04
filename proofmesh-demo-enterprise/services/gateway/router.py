"""
ProofMesh Demo Enterprise — API Gateway Router.
"""
from typing import Any, Dict
from services.auth.service import AuthService


class GatewayRouter:
    """Routes incoming external traffic through centralized authorization."""

    def __init__(self, auth_service: AuthService):
        self.auth = auth_service

    def handle_request(self, endpoint: str, user_id: str, org_id: str) -> Dict[str, Any]:
        """Dispatch request if authorized."""
        if not self.auth.authorize(user_id, org_id, "read"):
            return {"status": 403, "error": "Forbidden: Tenant Access Denied"}

        return {"status": 200, "data": f"Access granted to {endpoint}"}
