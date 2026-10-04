from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import HealthResponse, ReadyResponse
from app.services.jobs.queue import job_queue

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        service="proofmesh-api",
        version=settings.APP_VERSION,
    )


@router.get("/ready", response_model=ReadyResponse)
def readiness_check(response: Response, db: Session = Depends(get_db)):
    dependencies = {
        "postgres": "unknown",
        "redis": "unknown",
    }
    all_ready = True

    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        dependencies["postgres"] = "ok"
    except Exception:
        dependencies["postgres"] = "error"
        all_ready = False

    # Check Redis
    try:
        if job_queue.ping():
            dependencies["redis"] = "ok"
        else:
            dependencies["redis"] = "degraded"
    except Exception:
        dependencies["redis"] = "error"

    # Check Neo4j (Phase 2)
    try:
        from app.services.graph.neo4j_connection import Neo4jConnection
        neo4j_status = Neo4jConnection.health_check()
        dependencies["neo4j"] = "ok" if neo4j_status.get("status") == "healthy" else "unavailable"
    except Exception:
        dependencies["neo4j"] = "unavailable"

    status_str = "ready" if all_ready else "degraded"
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyResponse(status=status_str, dependencies=dependencies)
