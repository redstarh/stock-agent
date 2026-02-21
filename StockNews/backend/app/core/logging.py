"""Structured JSON logging configuration with request correlation."""

import logging
import sys
from contextvars import ContextVar

import structlog

# Context variable for request-scoped data
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
request_method_ctx: ContextVar[str] = ContextVar("request_method", default="")
request_path_ctx: ContextVar[str] = ContextVar("request_path", default="")


def add_request_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict,
) -> dict:
    """Add request context from contextvars to every log entry."""
    try:
        req_id = request_id_ctx.get("")
        if req_id:
            event_dict["request_id"] = req_id
        req_method = request_method_ctx.get("")
        if req_method:
            event_dict["request_method"] = req_method
        req_path = request_path_ctx.get("")
        if req_path:
            event_dict["request_path"] = req_path
    except (AttributeError, LookupError):
        # ContextVars may be unavailable during interpreter shutdown
        pass
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    json_output: bool = True,
    app_env: str = "production",
) -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_output: If True, output JSON; otherwise human-readable console output.
        app_env: Application environment name added to all log entries.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Shared processors for both structlog and stdlib
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_request_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog formatting
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    # Root handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "httpcore", "urllib3", "openai", "boto3", "botocore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Keep uvicorn.error at configured level
    logging.getLogger("uvicorn.error").setLevel(level)

    # Log startup
    startup_logger = structlog.get_logger("app.core.logging")
    startup_logger.info(
        "logging_configured",
        level=log_level.upper(),
        json_output=json_output,
        environment=app_env,
    )
