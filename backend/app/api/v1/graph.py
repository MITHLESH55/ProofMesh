"""
Phase 2 API — Graph & Impact Analysis Endpoints.

Provides endpoints for:
- Code dependency graph visualization
- Impact analysis for changed files
- File ingestion for graph building
- Graph statistics
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.errors import BadRequestError, NotFoundError
from app.core.logging import logger
from app.db.session import get_db
from app.schemas.common import SuccessEnvelope
from app.schemas.graph import (
    GraphResponse,
    GraphStatsResponse,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
    IngestFilesRequest,
    IngestFilesResponse,
    RiskSummary,
)
from app.services.analysis.source_parser import parse_file, detect_language, Language
from app.services.graph.graph_service import GraphService
from app.services.graph.neo4j_connection import Neo4jConnection
from app.services.impact.impact_analyzer import ImpactAnalyzer

router = APIRouter(prefix="/graph", tags=["Graph & Impact Analysis"])


@router.get(
    "/repository/{repository_id}",
    response_model=SuccessEnvelope[GraphResponse],
    summary="Get Repository Dependency Graph",
)
async def get_repository_graph(
    repository_id: str,
    limit: int = Query(default=200, ge=1, le=1000, description="Max nodes to return"),
):
    """Retrieve the full code dependency graph for a repository.

    Returns file nodes and their IMPORTS relationships for visualization.
    """
    try:
        GraphService.ensure_schema()
        graph_data = GraphService.get_repository_graph(repository_id, limit=limit)
        return SuccessEnvelope(
            data=GraphResponse(**graph_data),
            request_id="graph_repo",
        )
    except Exception as e:
        logger.error(f"Failed to retrieve repository graph: {e}", exc_info=True)
        raise BadRequestError(f"Failed to retrieve graph: {str(e)}", code="GRAPH_QUERY_FAILED")


@router.get(
    "/file/{repository_id}",
    response_model=SuccessEnvelope[GraphResponse],
    summary="Get File Dependency Graph",
)
async def get_file_graph(
    repository_id: str,
    file_path: str = Query(..., description="Path of the file to get dependencies for"),
    depth: int = Query(default=2, ge=1, le=5, description="Dependency traversal depth"),
):
    """Get the dependency graph centered on a specific file.

    Shows what the file imports, what defines it contains, and relationships.
    """
    try:
        GraphService.ensure_schema()
        graph_data = GraphService.get_file_dependencies(repository_id, file_path, depth=depth)
        return SuccessEnvelope(
            data=GraphResponse(**graph_data),
            request_id="graph_file",
        )
    except Exception as e:
        logger.error(f"Failed to retrieve file graph: {e}", exc_info=True)
        raise BadRequestError(f"Failed to retrieve file graph: {str(e)}", code="GRAPH_QUERY_FAILED")


@router.get(
    "/stats/{repository_id}",
    response_model=SuccessEnvelope[GraphStatsResponse],
    summary="Get Graph Statistics",
)
async def get_graph_stats(repository_id: str):
    """Get summary statistics for a repository's code graph."""
    try:
        GraphService.ensure_schema()
        stats = GraphService.get_graph_stats(repository_id)
        return SuccessEnvelope(
            data=GraphStatsResponse(**stats),
            request_id="graph_stats",
        )
    except Exception as e:
        logger.error(f"Failed to retrieve graph stats: {e}", exc_info=True)
        raise BadRequestError(f"Failed to retrieve stats: {str(e)}", code="GRAPH_QUERY_FAILED")


@router.post(
    "/impact/{repository_id}",
    response_model=SuccessEnvelope[ImpactAnalysisResponse],
    summary="Run Impact Analysis",
)
async def run_impact_analysis(
    repository_id: str,
    request: ImpactAnalysisRequest,
):
    """Analyze the impact of changed files on the codebase.

    Traces dependency chains to find directly and transitively impacted files,
    calculating risk scores for each.
    """
    try:
        GraphService.ensure_schema()
        analyzer = ImpactAnalyzer(repository_id, max_depth=request.max_depth)
        result = analyzer.analyze_changes(request.changed_files)
        result_dict = result.to_dict()

        return SuccessEnvelope(
            data=ImpactAnalysisResponse(
                repository_id=result_dict["repository_id"],
                changed_files=result_dict["changed_files"],
                directly_impacted=result_dict["directly_impacted"],
                transitively_impacted=result_dict["transitively_impacted"],
                total_files_affected=result_dict["total_files_affected"],
                risk_summary=RiskSummary(**result_dict["risk_summary"]),
            ),
            request_id="impact_analysis",
        )
    except Exception as e:
        logger.error(f"Impact analysis failed: {e}", exc_info=True)
        raise BadRequestError(f"Impact analysis failed: {str(e)}", code="IMPACT_ANALYSIS_FAILED")


@router.post(
    "/ingest",
    response_model=SuccessEnvelope[IngestFilesResponse],
    summary="Ingest Source Files into Graph",
)
async def ingest_files(request: IngestFilesRequest):
    """Parse source files and ingest their structural elements into the dependency graph.

    Accepts a list of files with their content, parses them for classes,
    functions, imports, etc., and creates/updates the Neo4j graph accordingly.
    """
    try:
        GraphService.ensure_schema()

        response = IngestFilesResponse(
            repository_id=request.repository_id,
            commit_sha=request.commit_sha,
        )

        for file_payload in request.files:
            language = detect_language(file_payload.path)
            if language == Language.UNKNOWN:
                continue

            analysis = parse_file(file_payload.path, file_payload.content)

            if analysis.errors:
                response.errors.extend(
                    [f"{file_payload.path}: {err}" for err in analysis.errors]
                )
                continue

            stats = GraphService.ingest_file_analysis(
                repository_id=request.repository_id,
                analysis=analysis,
                commit_sha=request.commit_sha,
            )

            response.files_processed += stats.get("files", 0)
            response.total_classes += stats.get("classes", 0)
            response.total_functions += stats.get("functions", 0)
            response.total_methods += stats.get("methods", 0)
            response.total_imports += stats.get("imports", 0)
            response.total_relationships += stats.get("relationships", 0)

        logger.info(
            f"File ingestion complete: {response.files_processed} files processed",
            extra={
                "repository_id": request.repository_id,
                "commit_sha": request.commit_sha,
                "stats": response.model_dump(),
            },
        )

        return SuccessEnvelope(
            data=response,
            request_id="ingest_files",
        )
    except Exception as e:
        logger.error(f"File ingestion failed: {e}", exc_info=True)
        raise BadRequestError(f"File ingestion failed: {str(e)}", code="INGESTION_FAILED")


@router.delete(
    "/repository/{repository_id}",
    summary="Clear Repository Graph",
)
async def clear_repository_graph(repository_id: str):
    """Delete all graph data for a repository."""
    try:
        result = GraphService.clear_repository_graph(repository_id)
        return SuccessEnvelope(
            data={"repository_id": repository_id, "deleted": True, "details": result},
            request_id="clear_graph",
        )
    except Exception as e:
        logger.error(f"Failed to clear graph: {e}", exc_info=True)
        raise BadRequestError(f"Failed to clear graph: {str(e)}", code="GRAPH_CLEAR_FAILED")


@router.get(
    "/health",
    summary="Graph Database Health Check",
)
async def graph_health():
    """Check Neo4j connectivity."""
    status = Neo4jConnection.health_check()
    return SuccessEnvelope(
        data=status,
        request_id="graph_health",
    )
