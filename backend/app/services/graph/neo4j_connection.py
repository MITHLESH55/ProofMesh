"""
Neo4j Graph Database Connection Manager.

Provides connection pooling, session management, and schema initialization
for the ProofMesh code dependency graph.
"""
import atexit
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase, Driver, Session as Neo4jSession
from neo4j.exceptions import ServiceUnavailable, AuthError
from app.core.config import settings
from app.core.logging import logger


class Neo4jConnection:
    """Manages Neo4j driver lifecycle, session creation, and schema constraints."""

    _driver: Optional[Driver] = None
    _initialized: bool = False

    @classmethod
    def get_driver(cls) -> Driver:
        """Get or create Neo4j driver with connection pooling."""
        if cls._driver is None:
            try:
                cls._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=30,
                )
                cls._driver.verify_connectivity()
                logger.info(
                    "Neo4j connection established",
                    extra={"uri": settings.NEO4J_URI, "database": settings.NEO4J_DATABASE},
                )
                atexit.register(cls.close)
            except AuthError as e:
                logger.error(f"Neo4j authentication failed: {e}")
                raise
            except ServiceUnavailable as e:
                logger.error(f"Neo4j service unavailable at {settings.NEO4J_URI}: {e}")
                raise
        return cls._driver

    @classmethod
    def get_session(cls, **kwargs) -> Neo4jSession:
        """Get a new Neo4j session."""
        driver = cls.get_driver()
        return driver.session(database=settings.NEO4J_DATABASE, **kwargs)

    @classmethod
    def close(cls) -> None:
        """Close the Neo4j driver."""
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
            cls._initialized = False
            logger.info("Neo4j connection closed")

    @classmethod
    def health_check(cls) -> Dict[str, Any]:
        """Check Neo4j connectivity and return status."""
        try:
            driver = cls.get_driver()
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("RETURN 1 AS health")
                record = result.single()
                if record and record["health"] == 1:
                    return {"status": "healthy", "uri": settings.NEO4J_URI}
            return {"status": "unhealthy", "uri": settings.NEO4J_URI}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "uri": settings.NEO4J_URI}

    @classmethod
    def initialize_schema(cls) -> None:
        """Create indexes and constraints for the graph schema.

        Node types:
        - (:File {path, repository_id, language, last_analyzed})
        - (:Function {name, file_path, repository_id, start_line, end_line, signature})
        - (:Class {name, file_path, repository_id, start_line, end_line})
        - (:Module {name, repository_id, path})
        - (:Repository {id, full_name})

        Relationship types:
        - (:File)-[:IMPORTS]->(:File)
        - (:File)-[:DEFINES]->(:Function)
        - (:File)-[:DEFINES]->(:Class)
        - (:Class)-[:HAS_METHOD]->(:Function)
        - (:Function)-[:CALLS]->(:Function)
        - (:Class)-[:INHERITS]->(:Class)
        - (:File)-[:BELONGS_TO]->(:Module)
        - (:Module)-[:BELONGS_TO]->(:Repository)
        - (:File)-[:BELONGS_TO]->(:Repository)
        """
        if cls._initialized:
            return

        constraints_and_indexes = [
            # Uniqueness constraints
            "CREATE CONSTRAINT file_unique IF NOT EXISTS FOR (f:File) REQUIRE (f.repository_id, f.path) IS UNIQUE",
            "CREATE CONSTRAINT function_unique IF NOT EXISTS FOR (fn:Function) REQUIRE (fn.repository_id, fn.file_path, fn.name, fn.start_line) IS UNIQUE",
            "CREATE CONSTRAINT class_unique IF NOT EXISTS FOR (c:Class) REQUIRE (c.repository_id, c.file_path, c.name) IS UNIQUE",
            "CREATE CONSTRAINT module_unique IF NOT EXISTS FOR (m:Module) REQUIRE (m.repository_id, m.path) IS UNIQUE",
            "CREATE CONSTRAINT repo_unique IF NOT EXISTS FOR (r:Repository) REQUIRE (r.id) IS UNIQUE",
            # Performance indexes
            "CREATE INDEX file_language IF NOT EXISTS FOR (f:File) ON (f.language)",
            "CREATE INDEX file_repo IF NOT EXISTS FOR (f:File) ON (f.repository_id)",
            "CREATE INDEX function_name IF NOT EXISTS FOR (fn:Function) ON (fn.name)",
            "CREATE INDEX class_name IF NOT EXISTS FOR (c:Class) ON (c.name)",
        ]

        try:
            with cls.get_session() as session:
                for stmt in constraints_and_indexes:
                    try:
                        session.run(stmt)
                    except Exception as e:
                        # Constraints may already exist
                        logger.debug(f"Schema statement skipped or failed: {stmt} -> {e}")
            cls._initialized = True
            logger.info("Neo4j schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema: {e}")
            raise


def execute_cypher(
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    write: bool = False,
) -> List[Dict[str, Any]]:
    """Execute a Cypher query and return results as list of dicts."""
    with Neo4jConnection.get_session() as session:
        if write:
            result = session.run(query, parameters or {})
        else:
            result = session.run(query, parameters or {})
        return [dict(record) for record in result]


def execute_cypher_write(
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a write Cypher query within a transaction and return summary."""
    with Neo4jConnection.get_session() as session:
        result = session.run(query, parameters or {})
        summary = result.consume()
        return {
            "nodes_created": summary.counters.nodes_created,
            "relationships_created": summary.counters.relationships_created,
            "nodes_deleted": summary.counters.nodes_deleted,
            "relationships_deleted": summary.counters.relationships_deleted,
            "properties_set": summary.counters.properties_set,
        }
