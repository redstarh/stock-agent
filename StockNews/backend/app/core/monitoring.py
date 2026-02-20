"""Error tracking and monitoring setup."""

import logging
from typing import Any

import sentry_sdk
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

logger = logging.getLogger(__name__)


def init_sentry(dsn: str | None, environment: str, debug: bool) -> None:
    """Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN (optional - app works without it)
        environment: Application environment (development/production)
        debug: Debug mode flag
    """
    if not dsn:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=1.0 if debug else 0.1,
            profiles_sample_rate=1.0 if debug else 0.1,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],
            # Don't send PII
            send_default_pii=False,
            # Set release version
            release=None,  # TODO: Set from env var or git tag
            # Limit breadcrumbs
            max_breadcrumbs=50,
            # Filter sensitive data
            before_send=_filter_sensitive_data,
        )
        logger.info(f"Sentry initialized for environment: {environment}")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def _filter_sensitive_data(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Filter sensitive data from Sentry events.

    Args:
        event: Sentry event data
        hint: Additional context

    Returns:
        Filtered event or None to drop the event
    """
    # Remove sensitive headers
    if "request" in event:
        headers = event["request"].get("headers", {})
        for sensitive_key in ["authorization", "x-api-key", "cookie"]:
            if sensitive_key in headers:
                headers[sensitive_key] = "[FILTERED]"

    # Remove query params that might contain API keys
    if "request" in event and "query_string" in event["request"]:
        query = event["request"]["query_string"]
        if "api_key" in query.lower() or "token" in query.lower():
            event["request"]["query_string"] = "[FILTERED]"

    return event


def setup_prometheus(app: Any) -> None:
    """Setup Prometheus metrics collection.

    Args:
        app: FastAPI application instance
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )

    # Instrument the app first
    instrumentator.instrument(app)
    # Then expose the metrics endpoint
    instrumentator.expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics instrumentation enabled at /metrics")


def sanitize_exception_message(exc: Exception, debug: bool) -> str:
    """Sanitize exception message for production.

    Args:
        exc: Exception to sanitize
        debug: Debug mode flag

    Returns:
        Sanitized error message
    """
    if debug:
        # In debug mode, return full exception details
        return str(exc)

    # In production, return generic message to avoid exposing internal details
    return "Internal Server Error"
