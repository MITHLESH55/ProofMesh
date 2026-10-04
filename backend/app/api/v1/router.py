from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.repositories import router as repo_router
from app.api.v1.changes import router as changes_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.health import router as health_router
from app.api.v1.graph import router as graph_router
from app.api.v1.assurance import router as assurance_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(repo_router)
api_v1_router.include_router(changes_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(graph_router)
api_v1_router.include_router(assurance_router)
