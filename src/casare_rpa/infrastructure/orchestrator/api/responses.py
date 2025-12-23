"""
Unified API response models for CasareRPA Orchestrator.

Provides consistent response structure across all endpoints:
- Success/error discrimination
- Pagination metadata
- Request tracking via request_id
- Standard error codes and details
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # Authentication/Authorization (4xx)
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    AUTH_TENANT_MISMATCH = "AUTH_TENANT_MISMATCH"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Resource errors (4xx)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # Validation errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


class ErrorDetail(BaseModel):
    """Structured error information."""

    code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error context")
    field: str | None = Field(None, description="Field causing the error")

    model_config = ConfigDict(use_enum_values=True)


class ResponseMeta(BaseModel):
    """Response metadata for tracking and pagination."""

    request_id: str = Field(..., description="Unique request identifier for tracing")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp (UTC)",
    )
    page: int | None = Field(None, ge=1, description="Current page number")
    page_size: int | None = Field(None, ge=1, le=1000, description="Items per page")
    total_items: int | None = Field(None, ge=0, description="Total items available")
    total_pages: int | None = Field(None, ge=0, description="Total pages available")

    @field_serializer("timestamp")
    def serialize_timestamp(self, v: datetime) -> str:
        """Serialize timestamp to ISO format."""
        return v.isoformat() + "Z" if v else None


class APIResponse(BaseModel, Generic[T]):
    """
    Unified API response wrapper.

    All API endpoints return this structure for consistency.
    The 'data' field contains the actual response payload.
    The 'error' field is populated only when success=False.
    """

    success: bool = Field(..., description="Whether the request succeeded")
    data: T | None = Field(None, description="Response payload (on success)")
    error: ErrorDetail | None = Field(None, description="Error details (on failure)")
    meta: ResponseMeta = Field(..., description="Response metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {"id": "abc-123", "name": "Example"},
                "error": None,
                "meta": {
                    "request_id": "req_abc123",
                    "timestamp": "2025-12-03T10:30:00Z",
                },
            }
        }
    )


class PaginatedResponse(APIResponse[list[T]], Generic[T]):
    """
    Paginated API response for list endpoints.

    Extends APIResponse with pagination-specific metadata.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": [{"id": "1"}, {"id": "2"}],
                "error": None,
                "meta": {
                    "request_id": "req_abc123",
                    "timestamp": "2025-12-03T10:30:00Z",
                    "page": 1,
                    "page_size": 50,
                    "total_items": 100,
                    "total_pages": 2,
                },
            }
        }
    )


# ============================================================================
# Response Factory Functions
# ============================================================================


def success_response(
    data: Any,
    request_id: str,
    page: int | None = None,
    page_size: int | None = None,
    total_items: int | None = None,
) -> dict:
    """
    Create a successful API response.

    Args:
        data: Response payload
        request_id: Request tracking ID
        page: Current page (for paginated responses)
        page_size: Items per page (for paginated responses)
        total_items: Total available items (for paginated responses)

    Returns:
        Response dictionary matching APIResponse structure
    """
    total_pages = None
    if page_size and total_items is not None:
        total_pages = (total_items + page_size - 1) // page_size

    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }


def error_response(
    code: ErrorCode,
    message: str,
    request_id: str,
    details: dict | None = None,
    field: str | None = None,
) -> dict:
    """
    Create an error API response.

    Args:
        code: Error code enum
        message: Human-readable error message
        request_id: Request tracking ID
        details: Additional error context
        field: Field causing the error (for validation errors)

    Returns:
        Response dictionary matching APIResponse structure
    """
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code.value if isinstance(code, ErrorCode) else code,
            "message": message,
            "details": details,
            "field": field,
        },
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }


# ============================================================================
# Common Response Models (for OpenAPI documentation)
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status: healthy, degraded, unhealthy")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")
    scheduler: str = Field(..., description="Scheduler status")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class ReadyResponse(BaseModel):
    """Readiness check response."""

    ready: bool = Field(..., description="Whether the service is ready to accept requests")
    checks: dict[str, bool] = Field(..., description="Individual readiness check results")


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str = Field(..., description="Response message")
    status: str = Field(default="success", description="Operation status")


# ============================================================================
# Type aliases for common response patterns
# ============================================================================

# For single item responses
SingleItemResponse = APIResponse[dict[str, Any]]

# For list responses with pagination
ListResponse = PaginatedResponse[dict[str, Any]]
