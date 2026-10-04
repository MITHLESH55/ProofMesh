"""
AI-Assisted Test Recommendation Service.

Generates targeted candidate test recommendations and executable test scaffolds
covering modified code paths, semantic contracts, and behavioral invariants.
"""
from typing import Any, Dict, List, Optional
from app.services.assurance.ai_provider import AIProvider, ProviderFactory


class TestRecommender:
    """Generates explainable test recommendations covering modified code paths."""
    __test__ = False

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self.ai_provider = ai_provider or ProviderFactory.get_provider()

    def generate_recommendations(
        self,
        changed_files: List[str],
        title: str = "",
        invariants: Optional[List[Dict[str, Any]]] = None,
        contracts: Optional[List[Dict[str, Any]]] = None,
        security_findings: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate structured test proposals covering modified behaviors and identified gaps."""
        recommendations: List[Dict[str, Any]] = []

        # 1. Deterministic invariant test coverage
        if invariants:
            for inv in invariants:
                comp = inv.get("affected_component", "auth")
                clean_comp = comp.replace("/", "_").replace(".py", "").replace(".ts", "")
                recommendations.append({
                    "target_component": comp,
                    "test_title": f"test_{clean_comp}_invariant_preservation",
                    "test_code_scaffold": (
                        f"def test_{clean_comp}_invariant_preservation(client):\n"
                        f"    \"\"\"Verify invariant: {inv.get('description')}\"\"\"\n"
                        f"    # 1. Test unauthorized actor receives 401/403\n"
                        f"    # 2. Test authorized actor with valid org membership succeeds\n"
                        f"    pass\n"
                    ),
                    "reason": f"Covers {inv.get('invariant_type', 'BEHAVIORAL')} invariant: {inv.get('description')}",
                    "invariant_covered": inv.get("description", "Security Invariant"),
                    "expected_behavior": "Strict access control enforced; unauthenticated access rejected.",
                    "confidence": 0.95,
                })

        # 2. Contract change test coverage
        if contracts:
            for c in contracts:
                path = c.get("endpoint_path", "/api/v1/resource")
                method = c.get("http_method", "GET")
                slug = path.strip("/").replace("/", "_").replace("*", "all")
                recommendations.append({
                    "target_component": f"{method} {path}",
                    "test_title": f"test_{method.lower()}_{slug}_contract_compatibility",
                    "test_code_scaffold": (
                        f"def test_{method.lower()}_{slug}_contract_compatibility(client, test_engineer_token):\n"
                        f"    \"\"\"Verify contract {c.get('classification')}: {method} {path}\"\"\"\n"
                        f"    headers = {{\"Authorization\": f\"Bearer {{test_engineer_token}}\"}}\n"
                        f"    response = client.{method.lower()}(\"{path}\", headers=headers)\n"
                        f"    assert response.status_code in [200, 201, 204]\n"
                    ),
                    "reason": f"Verifies API contract stability for {c.get('classification')} on {method} {path}",
                    "invariant_covered": "API Contract Stability",
                    "expected_behavior": "Payload structure and status codes match API contract specifications.",
                    "confidence": 0.90,
                })

        # 3. AI-proposed general recommendations
        ai_recs = self.ai_provider.recommend_tests({
            "changed_files": changed_files,
            "title": title,
        })
        for r in ai_recs:
            if not any(existing["test_title"] == r.get("test_title") for existing in recommendations):
                recommendations.append(r)

        return recommendations
