from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessEnvelope(BaseModel, Generic[T]):
    data: T
    request_id: str = Field(..., description="Unique request correlation ID")


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str
    details: Optional[dict[str, Any]] = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
