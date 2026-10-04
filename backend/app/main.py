from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import ProofMeshError
from app.core.logging import logger, setup_logging
from app.core.middleware import RequestIdMiddleware
from app.schemas.common import ErrorDetail, ErrorEnvelope

# Setup structured logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ProofMesh — AI-Native Software Change Assurance & Reliability Platform (Phase 1 Foundation)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID correlation middleware
app.add_middleware(RequestIdMiddleware)


# Standardized Exception Handlers
@app.exception_handler(ProofMeshError)
async def proofmesh_error_handler(request: Request, exc: ProofMeshError):
    request_id = getattr(request.state, "request_id", "req_unknown")
    logger.warning(
        f"Handled application error [{exc.code}]: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                request_id=request_id,
                details=exc.details,
            )
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "req_unknown")
    formatted_errors = [{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in exc.errors()]
    logger.warning(
        f"Validation error on {request.url.path}: {formatted_errors}",
        extra={"request_id": request_id, "errors": formatted_errors, "path": request.url.path}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorEnvelope(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request input validation failed",
                request_id=request_id,
                details={"errors": formatted_errors},
            )
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "req_unknown")
    logger.error(
        f"Unhandled server error on {request.url.path}: {str(exc)}",
        extra={"request_id": request_id, "path": request.url.path},
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorEnvelope(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal server error occurred",
                request_id=request_id,
            )
        ).model_dump(),
    )


# Include API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }
