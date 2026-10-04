import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging import logger


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:12]}"

        # Store in request state for downstream handlers
        request.state.request_id = request_id

        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"Unhandled exception during request {request.method} {request.url.path}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "event": "http_request_error",
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration, 2),
                },
                exc_info=True
            )
            raise exc

        duration = (time.time() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id

        # Log non-health endpoints at INFO level
        if not request.url.path.endswith("/health") and not request.url.path.endswith("/ready"):
            logger.info(
                f"{request.method} {request.url.path} {response.status_code} - {duration:.2f}ms",
                extra={
                    "request_id": request_id,
                    "event": "http_request_completed",
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration_ms": round(duration, 2),
                }
            )

        return response
