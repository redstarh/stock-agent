"""Tests for structured JSON logging configuration."""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest


class TestSetupLogging:
    """Test logging setup and configuration."""

    def test_json_output_format(self):
        """JSON mode produces valid JSON log entries."""
        from app.core.logging import setup_logging

        stream = StringIO()
        setup_logging(log_level="INFO", json_output=True, app_env="test")

        # Replace root handler with our stream
        handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        handler.setFormatter(formatter)
        root.handlers.clear()
        root.addHandler(handler)

        test_logger = logging.getLogger("test.json_output")
        test_logger.info("test message")

        output = stream.getvalue().strip()
        assert output, "Expected log output"

        parsed = json.loads(output)
        assert parsed["event"] == "test message"
        assert parsed["level"] == "info"
        assert "timestamp" in parsed

    def test_console_output_mode(self):
        """Console mode produces human-readable output (not JSON)."""
        from app.core.logging import setup_logging

        stream = StringIO()
        setup_logging(log_level="DEBUG", json_output=False, app_env="development")

        handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        handler.setFormatter(formatter)
        root.handlers.clear()
        root.addHandler(handler)

        test_logger = logging.getLogger("test.console_output")
        test_logger.info("hello console")

        output = stream.getvalue()
        assert "hello console" in output
        # Should NOT be valid JSON
        try:
            json.loads(output.strip())
            is_json = True
        except json.JSONDecodeError:
            is_json = False
        assert not is_json, "Console mode should not produce JSON"

    def test_log_level_filtering(self):
        """Log level properly filters messages."""
        from app.core.logging import setup_logging

        stream = StringIO()
        setup_logging(log_level="WARNING", json_output=True, app_env="test")

        handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        handler.setFormatter(formatter)
        root.handlers.clear()
        root.addHandler(handler)

        test_logger = logging.getLogger("test.level_filter")
        test_logger.debug("should not appear")
        test_logger.info("should not appear")
        test_logger.warning("should appear")

        lines = [l for l in stream.getvalue().strip().split("\n") if l]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event"] == "should appear"
        assert parsed["level"] == "warning"

    def test_noisy_loggers_suppressed(self):
        """Third-party loggers are set to WARNING level."""
        from app.core.logging import setup_logging

        setup_logging(log_level="DEBUG", json_output=True, app_env="test")

        for name in ("uvicorn.access", "httpx", "httpcore", "urllib3"):
            assert logging.getLogger(name).level >= logging.WARNING

    def test_logger_name_included(self):
        """Logger name is included in structured output."""
        from app.core.logging import setup_logging

        stream = StringIO()
        setup_logging(log_level="INFO", json_output=True, app_env="test")

        handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        handler.setFormatter(formatter)
        root.handlers.clear()
        root.addHandler(handler)

        test_logger = logging.getLogger("my.custom.logger")
        test_logger.info("named test")

        parsed = json.loads(stream.getvalue().strip())
        assert parsed["logger"] == "my.custom.logger"


class TestRequestContext:
    """Test request context variables."""

    def test_request_id_context(self):
        """Request ID is propagated to log entries via contextvars."""
        from app.core.logging import setup_logging, request_id_ctx

        stream = StringIO()
        setup_logging(log_level="INFO", json_output=True, app_env="test")

        handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        handler.setFormatter(formatter)
        root.handlers.clear()
        root.addHandler(handler)

        token = request_id_ctx.set("abc123")
        try:
            test_logger = logging.getLogger("test.request_ctx")
            test_logger.info("with request")
        finally:
            request_id_ctx.reset(token)

        parsed = json.loads(stream.getvalue().strip())
        assert parsed["request_id"] == "abc123"

    def test_empty_request_context_omitted(self):
        """When no request context is set, fields are omitted."""
        from app.core.logging import setup_logging, request_id_ctx

        stream = StringIO()
        setup_logging(log_level="INFO", json_output=True, app_env="test")

        handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        handler.setFormatter(formatter)
        root.handlers.clear()
        root.addHandler(handler)

        # Ensure context is empty
        request_id_ctx.set("")

        test_logger = logging.getLogger("test.no_ctx")
        test_logger.info("no request context")

        parsed = json.loads(stream.getvalue().strip())
        assert "request_id" not in parsed


class TestRequestMiddleware:
    """Test request logging middleware."""

    def test_middleware_adds_request_id_header(self):
        """Middleware adds X-Request-ID to response."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.core.middleware import RequestLoggingMiddleware

        test_app = FastAPI()
        test_app.add_middleware(RequestLoggingMiddleware)

        @test_app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(test_app)
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 8

    def test_middleware_preserves_incoming_request_id(self):
        """Middleware uses X-Request-ID from incoming request if provided."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.core.middleware import RequestLoggingMiddleware

        test_app = FastAPI()
        test_app.add_middleware(RequestLoggingMiddleware)

        @test_app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(test_app)
        response = client.get("/test", headers={"X-Request-ID": "custom-id"})
        assert response.headers["X-Request-ID"] == "custom-id"

    def test_middleware_logs_request_duration(self):
        """Middleware logs request with duration."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.core.middleware import RequestLoggingMiddleware
        from app.core.logging import setup_logging

        stream = StringIO()
        setup_logging(log_level="INFO", json_output=True, app_env="test")

        handler = logging.StreamHandler(stream)
        root = logging.getLogger()
        formatter = root.handlers[0].formatter
        handler.setFormatter(formatter)
        root.handlers.clear()
        root.addHandler(handler)

        test_app = FastAPI()
        test_app.add_middleware(RequestLoggingMiddleware)

        @test_app.get("/duration-test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(test_app)
        client.get("/duration-test")

        lines = [l for l in stream.getvalue().strip().split("\n") if l]
        # Find the request_completed log entry
        completed = None
        for line in lines:
            try:
                parsed = json.loads(line)
                if parsed.get("event") == "request_completed":
                    completed = parsed
                    break
            except json.JSONDecodeError:
                continue

        assert completed is not None, f"Expected request_completed log entry, got: {lines}"
        assert "duration_ms" in completed
        assert completed["status_code"] == 200
