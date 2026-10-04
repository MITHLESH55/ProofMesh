from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class ProofMeshError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(ProofMeshError):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnauthorizedError(ProofMeshError):
    def __init__(self, message: str = "Unauthorized", code: str = "UNAUTHORIZED"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(ProofMeshError):
    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class BadRequestError(ProofMeshError):
    def __init__(self, message: str = "Bad request", code: str = "BAD_REQUEST"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ConflictError(ProofMeshError):
    def __init__(self, message: str = "Resource conflict", code: str = "CONFLICT"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
        )


class WebhookError(ProofMeshError):
    def __init__(self, message: str = "Webhook processing failed", code: str = "INVALID_WEBHOOK_SIGNATURE"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
