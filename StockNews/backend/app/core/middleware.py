"""Request middleware for correlation and logging."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx, request_method_ctx, request_path_ctx

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Add request ID and log request/response lifecycle."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])

        # Set context vars for structured logging
        request_id_token = request_id_ctx.set(request_id)
        request_method_token = request_method_ctx.set(request.method)
        request_path_token = request_path_ctx.set(request.url.path)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)

            # Use structlog's bind pattern for proper key-value logging
            import structlog
            log = structlog.get_logger(__name__)
            log.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            # Use structlog for proper key-value logging
            import structlog
            log = structlog.get_logger(__name__)
            log.error(
                "request_failed",
                error=str(exc),
                duration_ms=duration_ms,
                exc_info=True,
            )
            raise

        finally:
            # Reset context vars
            request_id_ctx.reset(request_id_token)
            request_method_ctx.reset(request_method_token)
            request_path_ctx.reset(request_path_token)
