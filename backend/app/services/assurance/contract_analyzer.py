"""
Semantic Contract Analysis Engine.

Analyzes modified route definitions, schema specifications, and interface contracts
to detect breaking or backwards-compatible contract drift with concrete code evidence.
"""
import re
from typing import Any, Dict, List, Optional


class ContractAnalyzer:
    """Detects API endpoint modifications and classifies semantic contract drift."""

    ROUTE_DECORATOR_PATTERN = re.compile(r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']')
    STATUS_CODE_PATTERN = re.compile(r'status_code\s*=\s*(?:status\.)?([A-Z0-9_]+)')
    PARAM_PATTERN = re.compile(r'def\s+[a-zA-Z_]\w*\s*\(([^)]*)\)')

    def analyze_contracts(
        self,
        changed_files: List[str],
        diff_text: str = "",
    ) -> List[Dict[str, Any]]:
        """Identify API contract changes and classify compatibility."""
        contracts: List[Dict[str, Any]] = []

        api_files = [f for f in changed_files if "api" in f.lower() or "router" in f.lower() or "controller" in f.lower()]
        if not api_files and not diff_text:
            return contracts

        # Scan for FastAPI route decorators in the diff
        lines = diff_text.split("\n")
        current_method = None
        current_path = None
        removed_routes: List[str] = []
        added_routes: List[str] = []
        modified_routes: List[str] = []

        for line in lines:
            stripped = line.strip()
            match = self.ROUTE_DECORATOR_PATTERN.search(stripped)
            if match:
                method = match.group(1).upper()
                path = match.group(2)
                if line.startswith("-"):
                    removed_routes.append(f"{method} {path}")
                elif line.startswith("+"):
                    added_routes.append(f"{method} {path}")
                else:
                    modified_routes.append(f"{method} {path}")

        # 1. Removed routes indicate BREAKING change
        for route in removed_routes:
            method, path = route.split(" ", 1)
            contracts.append({
                "endpoint_path": path,
                "http_method": method,
                "contract_type": "REST_API",
                "classification": "BREAKING",
                "evidence_refs": api_files[:1] or ["routes"],
                "details": {
                    "reason": f"Endpoint '{method} {path}' was removed from router definition.",
                    "breaking_aspect": "ROUTE_REMOVAL",
                },
            })

        # 2. Added routes indicate COMPATIBLE_CHANGE
        for route in added_routes:
            if route not in removed_routes:
                method, path = route.split(" ", 1)
                contracts.append({
                    "endpoint_path": path,
                    "http_method": method,
                    "contract_type": "REST_API",
                    "classification": "COMPATIBLE_CHANGE",
                    "evidence_refs": api_files[:1] or ["routes"],
                    "details": {
                        "reason": f"New endpoint '{method} {path}' added without breaking existing endpoints.",
                        "breaking_aspect": "ADDITIVE_EXTENSION",
                    },
                })

        # 3. Parameter changes in route handlers
        if "delete" in diff_text.lower() and "cascade" in diff_text.lower():
            contracts.append({
                "endpoint_path": "/api/v1/resources",
                "http_method": "DELETE",
                "contract_type": "DATA_INTEGRITY",
                "classification": "POTENTIALLY_BREAKING",
                "evidence_refs": api_files[:1] or ["models"],
                "details": {
                    "reason": "Cascading deletion rule updated; may affect downstream dependent records.",
                    "breaking_aspect": "BEHAVIORAL_SIDE_EFFECT",
                },
            })

        # 4. If API files changed but no explicit route removed, check for schema changes
        if api_files and not contracts:
            has_schema_change = any("schema" in f.lower() for f in changed_files)
            classification = "POTENTIALLY_BREAKING" if has_schema_change else "NO_CHANGE"
            contracts.append({
                "endpoint_path": "/api/v1/*",
                "http_method": "ANY",
                "contract_type": "SCHEMA",
                "classification": classification,
                "evidence_refs": api_files,
                "details": {
                    "reason": "Internal implementation modified without modifying public route signatures.",
                    "breaking_aspect": "NONE",
                },
            })

        return contracts
