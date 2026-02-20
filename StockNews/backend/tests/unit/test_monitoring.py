"""Tests for monitoring module."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from app.core.monitoring import (
    init_sentry,
    sanitize_exception_message,
    setup_prometheus,
)


class TestSentryInit:
    """Test Sentry initialization."""

    def test_init_sentry_without_dsn(self):
        """Test Sentry init without DSN (app should work without it)."""
        # Should not raise, just log info
        init_sentry(dsn=None, environment="development", debug=True)
        init_sentry(dsn="", environment="development", debug=True)

    @patch("app.core.monitoring.sentry_sdk.init")
    def test_init_sentry_with_dsn(self, mock_sentry_init):
        """Test Sentry init with valid DSN."""
        dsn = "https://example@sentry.io/123"
        init_sentry(dsn=dsn, environment="production", debug=False)

        mock_sentry_init.assert_called_once()
        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["dsn"] == dsn
        assert call_kwargs["environment"] == "production"
        assert call_kwargs["traces_sample_rate"] == 0.1
        assert call_kwargs["profiles_sample_rate"] == 0.1

    @patch("app.core.monitoring.sentry_sdk.init")
    def test_init_sentry_debug_mode(self, mock_sentry_init):
        """Test Sentry init in debug mode (higher sampling rate)."""
        dsn = "https://example@sentry.io/123"
        init_sentry(dsn=dsn, environment="development", debug=True)

        mock_sentry_init.assert_called_once()
        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["traces_sample_rate"] == 1.0
        assert call_kwargs["profiles_sample_rate"] == 1.0

    @patch("app.core.monitoring.sentry_sdk.init")
    def test_init_sentry_handles_exception(self, mock_sentry_init):
        """Test Sentry init handles initialization errors gracefully."""
        mock_sentry_init.side_effect = Exception("Sentry init failed")

        # Should not raise, just log error
        init_sentry(dsn="https://example@sentry.io/123", environment="development", debug=True)


class TestSanitizeExceptionMessage:
    """Test exception message sanitization."""

    def test_sanitize_in_debug_mode(self):
        """Test that full exception is returned in debug mode."""
        exc = ValueError("Database connection failed: Invalid credentials")
        result = sanitize_exception_message(exc, debug=True)
        assert result == "Database connection failed: Invalid credentials"

    def test_sanitize_in_production_mode(self):
        """Test that generic message is returned in production."""
        exc = ValueError("Database connection failed: Invalid credentials")
        result = sanitize_exception_message(exc, debug=False)
        assert result == "Internal Server Error"

    def test_sanitize_with_sensitive_info(self):
        """Test that sensitive info is hidden in production."""
        exc = Exception("API key abc123 is invalid")
        result = sanitize_exception_message(exc, debug=False)
        assert "abc123" not in result
        assert result == "Internal Server Error"


class TestPrometheusSetup:
    """Test Prometheus setup."""

    def test_setup_prometheus(self):
        """Test Prometheus instrumentator setup."""
        app = FastAPI()
        setup_prometheus(app)

        # Verify metrics endpoint was added
        routes = [route.path for route in app.routes]
        assert "/metrics" in routes


class TestSentryDataFilter:
    """Test Sentry data filtering."""

    @patch("app.core.monitoring.sentry_sdk.init")
    def test_filter_sensitive_headers(self, mock_sentry_init):
        """Test that sensitive headers are filtered."""
        init_sentry(dsn="https://example@sentry.io/123", environment="production", debug=False)

        # Get the before_send callback
        call_kwargs = mock_sentry_init.call_args[1]
        before_send = call_kwargs["before_send"]

        # Create event with sensitive headers
        event = {
            "request": {
                "headers": {
                    "authorization": "Bearer secret-token",
                    "x-api-key": "api-key-123",
                    "content-type": "application/json",
                }
            }
        }

        filtered_event = before_send(event, {})

        # Check that sensitive headers are filtered
        assert filtered_event["request"]["headers"]["authorization"] == "[FILTERED]"
        assert filtered_event["request"]["headers"]["x-api-key"] == "[FILTERED]"
        assert filtered_event["request"]["headers"]["content-type"] == "application/json"

    @patch("app.core.monitoring.sentry_sdk.init")
    def test_filter_sensitive_query_params(self, mock_sentry_init):
        """Test that sensitive query params are filtered."""
        init_sentry(dsn="https://example@sentry.io/123", environment="production", debug=False)

        call_kwargs = mock_sentry_init.call_args[1]
        before_send = call_kwargs["before_send"]

        event = {
            "request": {
                "query_string": "api_key=secret123&stock=005930"
            }
        }

        filtered_event = before_send(event, {})
        assert filtered_event["request"]["query_string"] == "[FILTERED]"
