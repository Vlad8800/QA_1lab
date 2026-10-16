"""
Context management for Correlation ID tracing across async requests and tasks.
"""
from contextvars import ContextVar
from typing import Optional

_correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Retrieve the current correlation ID from context."""
    return _correlation_id_ctx.get()


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current async context."""
    return _correlation_id_ctx.set(correlation_id)


def clear_correlation_id():
    """Clear correlation ID."""
    _correlation_id_ctx.set(None)

