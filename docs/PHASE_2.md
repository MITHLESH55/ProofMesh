# ProofMesh — Phase 2 Specification: Code & Dependency Intelligence

## 1. Objective

Phase 2 introduces deep structural code comprehension and change-impact intelligence to ProofMesh. Building directly upon the Phase 1 change-ingestion platform, Phase 2 enables ProofMesh to parse multi-language source code, maintain a unified property graph of code dependencies in Neo4j, compute the exact transitive blast radius of pull request changes, and visualize dependency graphs interactively.

---

## 2. Architecture & Components

```text
Pull Request / Ingested Files
             │
             ▼
┌───────────────────────────────┐
│     Multi-Language Parser     │
│   (Python, TS/JS, Java, Go)   │
└──────────────┬────────────────┘
               │ Extracted Symbols:
               │ - File nodes
               │ - Class definitions
               │ - Functions & Methods
               │ - Imports & Calls
               ▼
┌───────────────────────────────┐
│     Graph Service (Neo4j)     │
│  Property Graph Constraints & │
│  Nodes: (:File), (:Function)  │
│  Edges: [:IMPORTS], [:DEFINES]│
└──────────────┬────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌─────────────────────────┐
│ Graph Query  │  │ Impact Analysis Engine  │
│ - Repo Graph │  │ - Multi-hop Traversal   │
│ - File Ego   │  │ - Affected Symbols      │
│ - Stats      │  │ - Risk & Blast Radius   │
└──────┬───────┘  └─────────────┬───────────┘
       │                        │
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │   FastAPI Endpoints    │
       │   (/api/v1/graph/*)    │
       └───────────┬────────────┘
                   ▼
       ┌────────────────────────┐
       │ React Canvas Graph UI  │
       │ Force-directed layout  │
       │ Impact simulation      │
       └────────────────────────┘
```

---

## 3. Implemented Capabilities

### 3.1 Multi-Language Source Code Parser
- **Location**: `backend/app/services/analysis/source_parser.py`
- Supports automatic language detection for `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`, and `.go`.
- Extracts:
  - Class definitions, inheritance bases, and docstrings.
  - Function and method declarations with signatures and start/end line bounds.
  - Import targets, aliasing, and module sources.
  - Call expressions for call graph modeling.
- Resilient to syntax errors; safely returns partial structural AST analysis without crashing.

### 3.2 Neo4j Graph Database
- **Location**: `backend/app/services/graph/neo4j_connection.py`, `backend/app/services/graph/graph_service.py`
- Connection pooling with health-check monitoring and schema management.
- Graph Schema:
  - **Node Labels**: `File`, `Function`, `Class`, `Module`, `Repository`
  - **Relationship Types**: `IMPORTS`, `DEFINES`, `HAS_METHOD`, `CALLS`, `INHERITS`, `BELONGS_TO`
  - **Constraints**: Uniqueness on `(repository_id, path)`, `(repository_id, file_path, name, start_line)`, etc.
  - **Indexes**: Indexed on `language`, `repository_id`, and symbol names.

### 3.3 Change Impact Analysis Engine
- **Location**: `backend/app/services/impact/impact_analyzer.py`
- Traces reverse dependencies through Cypher multi-hop traversals:
  - **Direct**: Modified files in the change set.
  - **First-Order**: Files that directly import modified files.
  - **Second-Order / Transitive**: Files affected via downstream import chains.
- Identifies affected functions and classes defined in impacted files.
- Computes honest risk scores based on graph proximity, blast radius, and dependency chains.

### 3.4 REST APIs
- `GET /api/v1/graph/repository/{repository_id}`: Overview graph of repository files and imports.
- `GET /api/v1/graph/file/{repository_id}`: File-centered dependency subgraph with definitions.
- `GET /api/v1/graph/stats/{repository_id}`: Aggregate statistics (files, classes, functions, imports).
- `POST /api/v1/graph/impact/{repository_id}`: Dynamic impact analysis for arbitrary changed files.
- `POST /api/v1/graph/ingest`: Direct ingestion of source files into Neo4j.
- `DELETE /api/v1/graph/repository/{repository_id}`: Graph purge for a repository.
- `GET /api/v1/graph/health`: Neo4j driver health check.

### 3.5 Worker Pipeline Integration
- Background worker advances change runs through the `DEPENDENCY_ANALYSIS` stage.
- Verifies graph connectivity and validates schema during processing.

### 3.6 Frontend Graph Visualization
- **Location**: `frontend/src/pages/DependencyGraph.tsx`
- Force-directed physics canvas supporting node dragging, zooming, panning, and selection.
- Color-coded node types (Files, Functions, Classes) with status badges and metrics.
- Integrated **Impact Simulation** panel to select changed files and evaluate transitive blast radius live.
- Direct **File Ingestion Modal** allowing developers to paste and ingest code directly from the UI.
- Integrated into the global navigation bar and route system (`/graph`).

---

## 4. Verification

- **Backend Tests**: 33 unit and API tests passing (`python -m pytest tests/backend`).
- **Frontend Build**: Zero TypeScript compilation or bundling errors (`npm run build`).
- **Phase 2 Boundaries**: Successfully completed without premature Phase 3 execution.
