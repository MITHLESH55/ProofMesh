"""
Impact Analysis Engine.

Determines which parts of the codebase are affected by a set of changed files,
using the dependency graph to trace transitive impact through imports,
function calls, and class hierarchies.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from app.core.logging import logger
from app.services.graph.neo4j_connection import execute_cypher


class ImpactLevel(str, Enum):
    DIRECT = "direct"       # File was directly changed
    FIRST_ORDER = "first"   # File directly imports a changed file
    SECOND_ORDER = "second" # File imports a file that imports a changed file
    TRANSITIVE = "transitive"  # Deeper transitive dependency


@dataclass
class ImpactedFile:
    """Represents a file impacted by a change.
    
    Note: `risk_score` represents structural impact proximity weight (0.0 - 1.0).
    Full semantic risk assessment is performed in Phase 3 by the Explainable Risk Engine.
    """
    path: str
    language: str
    impact_level: ImpactLevel
    impact_chain: List[str] = field(default_factory=list)  # Dependency chain from change
    affected_symbols: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # Structural impact proximity weight (0.0 - 1.0)

    @property
    def impact_weight(self) -> float:
        """Alias clarifying that Phase 2 calculates structural proximity weight."""
        return self.risk_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "language": self.language,
            "impact_level": self.impact_level.value,
            "impact_chain": self.impact_chain,
            "affected_symbols": self.affected_symbols,
            "risk_score": round(self.risk_score, 3),
            "impact_weight": round(self.risk_score, 3),
        }


@dataclass
class ImpactAnalysisResult:
    """Complete result of an impact analysis for a set of changes."""
    repository_id: str
    changed_files: List[str]
    directly_impacted: List[ImpactedFile] = field(default_factory=list)
    transitively_impacted: List[ImpactedFile] = field(default_factory=list)
    total_files_affected: int = 0
    risk_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository_id": self.repository_id,
            "changed_files": self.changed_files,
            "directly_impacted": [f.to_dict() for f in self.directly_impacted],
            "transitively_impacted": [f.to_dict() for f in self.transitively_impacted],
            "total_files_affected": self.total_files_affected,
            "risk_summary": self.risk_summary,
        }


class ImpactAnalyzer:
    """Analyzes the impact of code changes using the dependency graph."""

    def __init__(self, repository_id: str, max_depth: int = 4):
        self.repository_id = repository_id
        self.max_depth = max_depth

    def analyze_changes(
        self,
        changed_files: List[str],
    ) -> ImpactAnalysisResult:
        """Perform impact analysis for a list of changed file paths.

        Steps:
        1. Find direct dependents (files that IMPORT changed files)
        2. Trace transitive dependents up to max_depth
        3. Identify affected symbols in each impacted file
        4. Calculate risk scores
        """
        result = ImpactAnalysisResult(
            repository_id=self.repository_id,
            changed_files=changed_files,
        )

        if not changed_files:
            return result

        seen: Set[str] = set(changed_files)
        all_impacted: List[ImpactedFile] = []

        # Step 1: Find direct dependents (reverse imports)
        direct_deps = self._find_reverse_dependents(changed_files, depth=1)
        for dep_path, chain in direct_deps.items():
            if dep_path in seen:
                continue
            seen.add(dep_path)
            impacted = ImpactedFile(
                path=dep_path,
                language=self._get_file_language(dep_path),
                impact_level=ImpactLevel.FIRST_ORDER,
                impact_chain=chain,
                affected_symbols=self._get_affected_symbols(dep_path, changed_files),
                risk_score=self._calculate_risk(ImpactLevel.FIRST_ORDER, chain),
            )
            result.directly_impacted.append(impacted)
            all_impacted.append(impacted)

        # Step 2: Transitive dependents (depth 2+)
        if self.max_depth > 1:
            first_order_paths = [f.path for f in result.directly_impacted]
            if first_order_paths:
                for depth in range(2, self.max_depth + 1):
                    level = ImpactLevel.SECOND_ORDER if depth == 2 else ImpactLevel.TRANSITIVE
                    trans_deps = self._find_reverse_dependents(
                        first_order_paths if depth == 2 else [f.path for f in result.transitively_impacted[-50:]],
                        depth=1,
                    )
                    for dep_path, chain in trans_deps.items():
                        if dep_path in seen:
                            continue
                        seen.add(dep_path)
                        impacted = ImpactedFile(
                            path=dep_path,
                            language=self._get_file_language(dep_path),
                            impact_level=level,
                            impact_chain=chain,
                            risk_score=self._calculate_risk(level, chain),
                        )
                        result.transitively_impacted.append(impacted)
                        all_impacted.append(impacted)

        # Step 3: Calculate totals and risk summary
        result.total_files_affected = len(changed_files) + len(all_impacted)
        result.risk_summary = self._compute_risk_summary(changed_files, all_impacted)

        logger.info(
            f"Impact analysis complete for {len(changed_files)} changed files",
            extra={
                "repository_id": self.repository_id,
                "total_affected": result.total_files_affected,
                "direct": len(result.directly_impacted),
                "transitive": len(result.transitively_impacted),
            },
        )

        return result

    def _find_reverse_dependents(
        self,
        file_paths: List[str],
        depth: int = 1,
    ) -> Dict[str, List[str]]:
        """Find files that depend on the given files (reverse IMPORTS)."""
        results = execute_cypher(
            """
            UNWIND $paths AS changed_path
            MATCH (changed:File {repository_id: $repo_id, path: changed_path})
            MATCH (dependent:File)-[:IMPORTS*1..%d]->(changed)
            WHERE dependent.repository_id = $repo_id
            RETURN DISTINCT dependent.path AS dep_path,
                   changed_path AS source,
                   dependent.language AS language
            """ % depth,
            {"repo_id": self.repository_id, "paths": file_paths},
        )

        deps: Dict[str, List[str]] = {}
        for record in results:
            dep_path = record.get("dep_path", "")
            source = record.get("source", "")
            if dep_path and dep_path not in file_paths:
                if dep_path not in deps:
                    deps[dep_path] = []
                deps[dep_path].append(source)
        return deps

    def _get_affected_symbols(
        self, file_path: str, changed_files: List[str]
    ) -> List[str]:
        """Get symbols in file_path that use imports from changed files."""
        results = execute_cypher(
            """
            MATCH (f:File {repository_id: $repo_id, path: $path})-[:DEFINES]->(sym)
            WHERE (sym:Function OR sym:Class)
            RETURN sym.name AS name, labels(sym)[0] AS kind
            LIMIT 20
            """,
            {"repo_id": self.repository_id, "path": file_path},
        )
        return [f"{r.get('kind', '')}:{r.get('name', '')}" for r in results]

    def _get_file_language(self, file_path: str) -> str:
        """Get the language of a file from the graph."""
        results = execute_cypher(
            "MATCH (f:File {repository_id: $repo_id, path: $path}) RETURN f.language AS lang LIMIT 1",
            {"repo_id": self.repository_id, "path": file_path},
        )
        return results[0].get("lang", "unknown") if results else "unknown"

    @staticmethod
    def _calculate_risk(level: ImpactLevel, chain: List[str]) -> float:
        """Calculate a risk score based on impact level and chain depth."""
        base_scores = {
            ImpactLevel.DIRECT: 1.0,
            ImpactLevel.FIRST_ORDER: 0.8,
            ImpactLevel.SECOND_ORDER: 0.5,
            ImpactLevel.TRANSITIVE: 0.3,
        }
        base = base_scores.get(level, 0.2)
        # Reduce risk for longer chains (less direct impact)
        chain_penalty = max(0.0, 1.0 - (len(chain) * 0.1))
        return round(base * chain_penalty, 3)

    @staticmethod
    def _compute_risk_summary(
        changed_files: List[str],
        impacted: List[ImpactedFile],
    ) -> Dict[str, Any]:
        """Compute aggregate risk metrics."""
        if not impacted:
            return {
                "overall_risk": "low",
                "risk_score": 0.0,
                "high_risk_files": 0,
                "medium_risk_files": 0,
                "low_risk_files": 0,
                "blast_radius": len(changed_files),
            }

        high = sum(1 for f in impacted if f.risk_score >= 0.7)
        medium = sum(1 for f in impacted if 0.4 <= f.risk_score < 0.7)
        low = sum(1 for f in impacted if f.risk_score < 0.4)
        avg_risk = sum(f.risk_score for f in impacted) / len(impacted)

        if avg_risk >= 0.7 or high >= 5:
            overall = "critical"
        elif avg_risk >= 0.5 or high >= 2:
            overall = "high"
        elif avg_risk >= 0.3:
            overall = "medium"
        else:
            overall = "low"

        return {
            "overall_risk": overall,
            "risk_score": round(avg_risk, 3),
            "high_risk_files": high,
            "medium_risk_files": medium,
            "low_risk_files": low,
            "blast_radius": len(changed_files) + len(impacted),
        }
