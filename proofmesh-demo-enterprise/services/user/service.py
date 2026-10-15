"""
ProofMesh Demo Enterprise — User Profile Service.

Owns user-db (profile, preferences). Identity/credentials live in auth-db and
are NOT duplicated here. PII stored here must never flow to analytics (DATA-007).
"""
from typing import Dict, Optional


class UserService:
    """Manages non-credential user profile data within a tenant."""

    def __init__(self) -> None:
        self.profiles: Dict[str, Dict[str, str]] = {}

    def upsert_profile(self, user_id: str, organization_id: str, full_name: str, email: str) -> None:
        self.profiles[user_id] = {
            "organization_id": organization_id,
            "full_name": full_name,
            "email": email,
        }

    def get_profile(self, user_id: str, organization_id: str) -> Optional[Dict[str, str]]:
        """Return a profile only when the caller's tenant matches the record."""
        profile = self.profiles.get(user_id)
        if not profile or profile.get("organization_id") != organization_id:
            return None
        return profile
