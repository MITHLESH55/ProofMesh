"""
Graph Service — Manages the code dependency graph in Neo4j.

Provides operations to ingest parsed source structures into the graph,
query relationships, and retrieve subgraphs for visualization.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from app.core.logging import logger
from app.services.analysis.source_parser import FileAnalysis, SymbolInfo
from app.services.graph.neo4j_connection import (
    Neo4jConnection,
    execute_cypher,
    execute_cypher_write,
)


class GraphService:
    """Service for managing the code dependency graph."""

    @staticmethod
    def ensure_schema() -> None:
        """Ensure graph schema constraints and indexes exist."""
        Neo4jConnection.initialize_schema()

    @staticmethod
    def ingest_file_analysis(
        repository_id: str,
        analysis: FileAnalysis,
        commit_sha: str,
    ) -> Dict[str, Any]:
        """Ingest a parsed file's symbols and relationships into the graph.

        Creates/updates:
        - File node
        - Class nodes with DEFINES relationships
        - Function nodes with DEFINES relationships
        - Method nodes with HAS_METHOD relationships
        - Import relationships (IMPORTS)

        Returns summary of graph mutations.
        """
        stats = {
            "files": 0,
            "classes": 0,
            "functions": 0,
            "methods": 0,
            "imports": 0,
            "relationships": 0,
        }

        try:
            now = datetime.now(timezone.utc).isoformat()

            # 1. Create/update File node
            execute_cypher_write(
                """
                MERGE (f:File {repository_id: $repo_id, path: $path})
                SET f.language = $language,
                    f.last_analyzed = $now,
                    f.commit_sha = $commit_sha
                """,
                {
                    "repo_id": repository_id,
                    "path": analysis.file_path,
                    "language": analysis.language.value,
                    "now": now,
                    "commit_sha": commit_sha,
                },
            )
            stats["files"] = 1

            # 2. Ensure Repository node exists and link
            execute_cypher_write(
                """
                MERGE (r:Repository {id: $repo_id})
                WITH r
                MATCH (f:File {repository_id: $repo_id, path: $path})
                MERGE (f)-[:BELONGS_TO]->(r)
                """,
                {"repo_id": repository_id, "path": analysis.file_path},
            )

            # 3. Ingest classes
            for cls in analysis.classes:
                execute_cypher_write(
                    """
                    MERGE (c:Class {repository_id: $repo_id, file_path: $file_path, name: $name})
                    SET c.start_line = $start_line,
                        c.end_line = $end_line,
                        c.signature = $signature,
                        c.last_analyzed = $now
                    WITH c
                    MATCH (f:File {repository_id: $repo_id, path: $file_path})
                    MERGE (f)-[:DEFINES]->(c)
                    """,
                    {
                        "repo_id": repository_id,
                        "file_path": analysis.file_path,
                        "name": cls.name,
                        "start_line": cls.start_line,
                        "end_line": cls.end_line,
                        "signature": cls.signature,
                        "now": now,
                    },
                )
                stats["classes"] += 1
                stats["relationships"] += 1

            # 4. Ingest standalone functions
            for func in analysis.functions:
                execute_cypher_write(
                    """
                    MERGE (fn:Function {repository_id: $repo_id, file_path: $file_path, name: $name, start_line: $start_line})
                    SET fn.end_line = $end_line,
                        fn.signature = $signature,
                        fn.last_analyzed = $now
                    WITH fn
                    MATCH (f:File {repository_id: $repo_id, path: $file_path})
                    MERGE (f)-[:DEFINES]->(fn)
                    """,
                    {
                        "repo_id": repository_id,
                        "file_path": analysis.file_path,
                        "name": func.name,
                        "start_line": func.start_line,
                        "end_line": func.end_line,
                        "signature": func.signature,
                        "now": now,
                    },
                )
                stats["functions"] += 1
                stats["relationships"] += 1

            # 5. Ingest methods (linked to parent class)
            for method in analysis.methods:
                execute_cypher_write(
                    """
                    MERGE (fn:Function {repository_id: $repo_id, file_path: $file_path, name: $name, start_line: $start_line})
                    SET fn.end_line = $end_line,
                        fn.signature = $signature,
                        fn.is_method = true,
                        fn.parent_class = $parent,
                        fn.last_analyzed = $now
                    WITH fn
                    MATCH (c:Class {repository_id: $repo_id, file_path: $file_path, name: $parent})
                    MERGE (c)-[:HAS_METHOD]->(fn)
                    """,
                    {
                        "repo_id": repository_id,
                        "file_path": analysis.file_path,
                        "name": method.name,
                        "start_line": method.start_line,
                        "end_line": method.end_line,
                        "signature": method.signature,
                        "parent": method.parent or "",
                        "now": now,
                    },
                )
                stats["methods"] += 1
                stats["relationships"] += 1

            # 6. Ingest imports as IMPORTS relationships
            for imp in analysis.imports:
                # Resolve import to a file path within the repo
                target_path = GraphService._resolve_import_path(
                    imp.name, analysis.file_path, repository_id
                )
                if target_path:
                    execute_cypher_write(
                        """
                        MERGE (target:File {repository_id: $repo_id, path: $target_path})
                        WITH target
                        MATCH (source:File {repository_id: $repo_id, path: $source_path})
                        MERGE (source)-[:IMPORTS]->(target)
                        """,
                        {
                            "repo_id": repository_id,
                            "source_path": analysis.file_path,
                            "target_path": target_path,
                        },
                    )
                    stats["imports"] += 1
                    stats["relationships"] += 1

            logger.info(
                f"Graph ingestion complete for {analysis.file_path}",
                extra={"stats": stats, "repository_id": repository_id},
            )
            return stats

        except Exception as e:
            logger.error(
                f"Graph ingestion failed for {analysis.file_path}: {e}",
                extra={"repository_id": repository_id},
                exc_info=True,
            )
            raise

    @staticmethod
    def _resolve_import_path(
        import_name: str, source_file: str, repository_id: str
    ) -> Optional[str]:
        """Attempt to resolve an import name to a file path.

        Handles relative imports (e.g., './utils') and module-style imports
        (e.g., 'app.core.config' -> 'app/core/config.py').
        """
        if not import_name:
            return None

        # Skip external packages (no dots, not relative)
        if import_name.startswith("."):
            # Relative import: resolve against source file directory
            source_dir = "/".join(source_file.split("/")[:-1])
            relative = import_name.lstrip(".")
            if relative:
                path = f"{source_dir}/{relative.replace('.', '/')}"
            else:
                path = source_dir
        elif "." in import_name:
            # Module-style: app.core.config -> app/core/config
            path = import_name.replace(".", "/")
        else:
            # Could be a local file import or external package
            source_dir = "/".join(source_file.split("/")[:-1])
            path = f"{source_dir}/{import_name}" if source_dir else import_name

        # Try common extensions
        for ext in [".py", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js", "/__init__.py"]:
            candidate = path + ext
            # Check if the file exists in the graph
            result = execute_cypher(
                "MATCH (f:File {repository_id: $repo_id, path: $path}) RETURN f.path AS path LIMIT 1",
                {"repo_id": repository_id, "path": candidate},
            )
            if result:
                return result[0]["path"]

        # Return the basic .py path as a best-effort guess for new files
        if source_file.endswith(".py"):
            return path + ".py"
        elif source_file.endswith((".ts", ".tsx")):
            return path + ".ts"
        elif source_file.endswith((".js", ".jsx")):
            return path + ".js"
        return None

    @staticmethod
    def get_file_dependencies(
        repository_id: str, file_path: str, depth: int = 2
    ) -> Dict[str, Any]:
        """Get dependency graph for a specific file.

        Returns nodes and edges for visualization, traversing
        IMPORTS, DEFINES, and HAS_METHOD relationships up to `depth` levels.
        """
        query = """
        MATCH (source:File {repository_id: $repo_id, path: $path})
        OPTIONAL MATCH path_imports = (source)-[:IMPORTS*1..%d]->(imported:File)
        OPTIONAL MATCH (source)-[:DEFINES]->(symbol)
        WHERE symbol:Function OR symbol:Class
        WITH source, collect(DISTINCT imported) AS imports,
             collect(DISTINCT {name: symbol.name, kind: labels(symbol)[0], file_path: symbol.file_path, start_line: symbol.start_line}) AS symbols,
             collect(DISTINCT relationships(path_imports)) AS import_rels
        RETURN source, imports, symbols
        """ % depth

        results = execute_cypher(
            query,
            {"repo_id": repository_id, "path": file_path},
        )

        nodes = []
        edges = []
        seen_nodes: Set[str] = set()

        for record in results:
            source = record.get("source")
            if source:
                source_props = dict(source) if hasattr(source, "__iter__") else {}
                source_id = f"file:{file_path}"
                if source_id not in seen_nodes:
                    nodes.append({
                        "id": source_id,
                        "label": file_path.split("/")[-1],
                        "type": "file",
                        "path": file_path,
                        **source_props,
                    })
                    seen_nodes.add(source_id)

            for imp in record.get("imports", []):
                if imp is None:
                    continue
                imp_props = dict(imp) if hasattr(imp, "__iter__") else {}
                imp_path = imp_props.get("path", "")
                imp_id = f"file:{imp_path}"
                if imp_id not in seen_nodes:
                    nodes.append({
                        "id": imp_id,
                        "label": imp_path.split("/")[-1] if imp_path else "unknown",
                        "type": "file",
                        "path": imp_path,
                    })
                    seen_nodes.add(imp_id)
                edges.append({
                    "source": source_id,
                    "target": imp_id,
                    "relationship": "IMPORTS",
                })

            for sym in record.get("symbols", []):
                if sym is None:
                    continue
                sym_name = sym.get("name", "")
                sym_kind = sym.get("kind", "Function").lower()
                sym_id = f"{sym_kind}:{file_path}:{sym_name}"
                if sym_id not in seen_nodes:
                    nodes.append({
                        "id": sym_id,
                        "label": sym_name,
                        "type": sym_kind,
                        "file_path": file_path,
                        "start_line": sym.get("start_line"),
                    })
                    seen_nodes.add(sym_id)
                edges.append({
                    "source": source_id,
                    "target": sym_id,
                    "relationship": "DEFINES",
                })

        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def get_repository_graph(
        repository_id: str,
        limit: int = 200,
    ) -> Dict[str, Any]:
        """Get the full dependency graph for a repository.

        Returns a limited set of nodes and edges for overview visualization.
        """
        # Get files with their imports
        results = execute_cypher(
            """
            MATCH (f:File {repository_id: $repo_id})
            OPTIONAL MATCH (f)-[:IMPORTS]->(imported:File)
            OPTIONAL MATCH (f)-[:DEFINES]->(symbol)
            WHERE symbol:Function OR symbol:Class
            WITH f, collect(DISTINCT imported.path) AS imports,
                 count(DISTINCT symbol) AS symbol_count
            RETURN f.path AS path, f.language AS language,
                   imports, symbol_count
            ORDER BY symbol_count DESC
            LIMIT $limit
            """,
            {"repo_id": repository_id, "limit": limit},
        )

        nodes = []
        edges = []
        seen_nodes: Set[str] = set()

        for record in results:
            path = record.get("path", "")
            node_id = f"file:{path}"
            if node_id not in seen_nodes:
                nodes.append({
                    "id": node_id,
                    "label": path.split("/")[-1] if path else "unknown",
                    "type": "file",
                    "path": path,
                    "language": record.get("language", ""),
                    "symbol_count": record.get("symbol_count", 0),
                })
                seen_nodes.add(node_id)

            for imp_path in record.get("imports", []):
                if not imp_path:
                    continue
                imp_id = f"file:{imp_path}"
                if imp_id not in seen_nodes:
                    nodes.append({
                        "id": imp_id,
                        "label": imp_path.split("/")[-1],
                        "type": "file",
                        "path": imp_path,
                    })
                    seen_nodes.add(imp_id)
                edges.append({
                    "source": node_id,
                    "target": imp_id,
                    "relationship": "IMPORTS",
                })

        return {"nodes": nodes, "edges": edges, "total_files": len(nodes)}

    @staticmethod
    def get_graph_stats(repository_id: str) -> Dict[str, Any]:
        """Get summary statistics for a repository's code graph."""
        stats_query = """
        MATCH (f:File {repository_id: $repo_id})
        OPTIONAL MATCH (f)-[:DEFINES]->(fn:Function)
        OPTIONAL MATCH (f)-[:DEFINES]->(c:Class)
        OPTIONAL MATCH (f)-[:IMPORTS]->(imported:File)
        RETURN
            count(DISTINCT f) AS total_files,
            count(DISTINCT fn) AS total_functions,
            count(DISTINCT c) AS total_classes,
            count(DISTINCT imported) AS total_imports
        """
        results = execute_cypher(stats_query, {"repo_id": repository_id})

        if results:
            return {
                "repository_id": repository_id,
                "total_files": results[0].get("total_files", 0),
                "total_functions": results[0].get("total_functions", 0),
                "total_classes": results[0].get("total_classes", 0),
                "total_import_edges": results[0].get("total_imports", 0),
            }
        return {
            "repository_id": repository_id,
            "total_files": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_import_edges": 0,
        }

    @staticmethod
    def clear_repository_graph(repository_id: str) -> Dict[str, Any]:
        """Remove all graph data for a repository."""
        result = execute_cypher_write(
            """
            MATCH (n {repository_id: $repo_id})
            DETACH DELETE n
            """,
            {"repo_id": repository_id},
        )
        logger.info(f"Cleared graph data for repository {repository_id}", extra={"result": result})
        return result
