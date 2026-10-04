"""
Pydantic schemas for Phase 2 — Graph & Impact Analysis API.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Graph Schemas ---

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "file", "function", "class"
    path: Optional[str] = None
    file_path: Optional[str] = None
    language: Optional[str] = None
    start_line: Optional[int] = None
    symbol_count: Optional[int] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str  # "IMPORTS", "DEFINES", "HAS_METHOD", "CALLS"


class GraphResponse(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    total_files: Optional[int] = None


class GraphStatsResponse(BaseModel):
    repository_id: str
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_import_edges: int = 0


# --- Impact Analysis Schemas ---

class ImpactedFileResponse(BaseModel):
    path: str
    language: str
    impact_level: str  # "direct", "first", "second", "transitive"
    impact_chain: List[str] = Field(default_factory=list)
    affected_symbols: List[str] = Field(default_factory=list)
    risk_score: float = 0.0


class RiskSummary(BaseModel):
    overall_risk: str = "low"  # "low", "medium", "high", "critical"
    risk_score: float = 0.0
    high_risk_files: int = 0
    medium_risk_files: int = 0
    low_risk_files: int = 0
    blast_radius: int = 0


class ImpactAnalysisResponse(BaseModel):
    repository_id: str
    changed_files: List[str] = Field(default_factory=list)
    directly_impacted: List[ImpactedFileResponse] = Field(default_factory=list)
    transitively_impacted: List[ImpactedFileResponse] = Field(default_factory=list)
    total_files_affected: int = 0
    risk_summary: RiskSummary = Field(default_factory=RiskSummary)


class ImpactAnalysisRequest(BaseModel):
    changed_files: List[str] = Field(
        ...,
        description="List of file paths that were changed in the PR",
        min_length=1,
    )
    max_depth: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum depth for transitive dependency traversal",
    )


# --- File Ingestion Schemas ---

class FileContentPayload(BaseModel):
    path: str = Field(..., description="File path within the repository")
    content: str = Field(..., description="Source code content of the file")


class IngestFilesRequest(BaseModel):
    repository_id: str = Field(..., description="Repository ID to ingest files for")
    commit_sha: str = Field(..., description="Commit SHA associated with these files")
    files: List[FileContentPayload] = Field(
        ...,
        description="List of files with their content to parse and ingest",
        min_length=1,
    )


class IngestFilesResponse(BaseModel):
    repository_id: str
    commit_sha: str
    files_processed: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_methods: int = 0
    total_imports: int = 0
    total_relationships: int = 0
    errors: List[str] = Field(default_factory=list)
