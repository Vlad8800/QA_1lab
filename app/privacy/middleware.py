"""
FastAPI Middleware for correlation ID tracking and privacy-safe request auditing.
Prevents excessive logging of full request/response payloads while capturing vital audit metrics.
"""
import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.privacy.context import set_correlation_id
from app.privacy.sanitizer import mask_ip

logger = logging.getLogger("app.access")


class PrivacyLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages Correlation IDs and logs privacy-safe audit trails.
    Strictly avoids dumping raw request/response bodies to prevent PII exposure.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        set_correlation_id(correlation_id)

        start_time = time.perf_counter()
        client_host = request.client.host if request.client else "unknown"
        masked_client = mask_ip(client_host) if client_host != "unknown" else "unknown"

        # Safe inbound request audit log (Only technical metadata, NO raw body)
        logger.info(
            "Inbound HTTP request started",
            extra={
                "event_type": "HTTP_REQUEST_START",
                "method": request.method,
                "path": request.url.path,
                "client_ip": masked_client,
                "correlation_id": correlation_id,
            }
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Safe outbound response audit log (Status & duration, NO raw body)
            logger.info(
                "Inbound HTTP request finished",
                extra={
                    "event_type": "HTTP_REQUEST_FINISH",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "correlation_id": correlation_id,
                }
            )

            response.headers["X-Correlation-ID"] = correlation_id
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "Unhandled error during HTTP request execution",
                extra={
                    "event_type": "HTTP_REQUEST_ERROR",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                }
            )
            raise

