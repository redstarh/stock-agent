"""Verification scheduler 테스트."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apscheduler.schedulers.background import BackgroundScheduler

from app.collectors.verification_scheduler import (
    _verify_kr_job,
    _verify_us_job,
    register_verification_jobs,
)
from app.models.verification import VerificationRunLog


def test_register_verification_jobs():
    """Test verification jobs registration."""
    scheduler = BackgroundScheduler()

    register_verification_jobs(scheduler)

    # Check that both jobs are registered
    jobs = scheduler.get_jobs()
    job_ids = [job.id for job in jobs]

    assert "kr_verification" in job_ids
    assert "us_verification" in job_ids

    # Check job details
    kr_job = scheduler.get_job("kr_verification")
    assert kr_job is not None
    assert kr_job.name == "KR Market Verification"
    assert kr_job.max_instances == 1

    us_job = scheduler.get_job("us_verification")
    assert us_job is not None
    assert us_job.name == "US Market Verification"
    assert us_job.max_instances == 1


@patch("app.collectors.verification_scheduler.SessionLocal")
@patch("app.collectors.verification_scheduler.run_verification", new_callable=AsyncMock)
@patch("app.collectors.verification_scheduler.aggregate_theme_accuracy")
def test_verify_kr_job(mock_aggregate, mock_run_verification, mock_session_local):
    """Test KR verification job execution."""
    # Setup mocks
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_log = VerificationRunLog(
        run_date=date.today(),
        market="KR",
        status="success",
        stocks_verified=10,
        stocks_failed=0,
        duration_seconds=15.0,
    )
    mock_run_verification.return_value = mock_log

    # Execute job
    _verify_kr_job()

    # Verify calls
    mock_run_verification.assert_called_once()
    call_args = mock_run_verification.call_args[0]
    assert call_args[1] == date.today()  # target date
    assert call_args[2] == "KR"  # market

    mock_aggregate.assert_called_once()
    aggregate_args = mock_aggregate.call_args[0]
    assert aggregate_args[1] == date.today()
    assert aggregate_args[2] == "KR"

    mock_db.close.assert_called_once()


@patch("app.collectors.verification_scheduler.SessionLocal")
@patch("app.collectors.verification_scheduler.run_verification", new_callable=AsyncMock)
@patch("app.collectors.verification_scheduler.aggregate_theme_accuracy")
def test_verify_us_job(mock_aggregate, mock_run_verification, mock_session_local):
    """Test US verification job execution."""
    # Setup mocks
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_log = VerificationRunLog(
        run_date=date.today(),
        market="US",
        status="success",
        stocks_verified=8,
        stocks_failed=0,
        duration_seconds=20.0,
    )
    mock_run_verification.return_value = mock_log

    # Execute job
    _verify_us_job()

    # Verify calls
    mock_run_verification.assert_called_once()
    call_args = mock_run_verification.call_args[0]
    assert call_args[1] == date.today()
    assert call_args[2] == "US"

    mock_aggregate.assert_called_once()
    aggregate_args = mock_aggregate.call_args[0]
    assert aggregate_args[1] == date.today()
    assert aggregate_args[2] == "US"

    mock_db.close.assert_called_once()


@patch("app.collectors.verification_scheduler.SessionLocal")
@patch("app.collectors.verification_scheduler.run_verification", new_callable=AsyncMock)
@patch("app.collectors.verification_scheduler.aggregate_theme_accuracy")
def test_verify_job_failure_handling(
    mock_aggregate, mock_run_verification, mock_session_local
):
    """Test verification job handles failures gracefully."""
    # Setup mocks
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_log = VerificationRunLog(
        run_date=date.today(),
        market="KR",
        status="failed",
        stocks_verified=0,
        stocks_failed=5,
        duration_seconds=10.0,
        error_details="Price fetch failed",
    )
    mock_run_verification.return_value = mock_log

    # Execute job
    _verify_kr_job()

    # Verify that aggregate_theme_accuracy is NOT called when status is failed
    mock_run_verification.assert_called_once()
    mock_aggregate.assert_not_called()

    mock_db.close.assert_called_once()


@patch("app.collectors.verification_scheduler.SessionLocal")
@patch("app.collectors.verification_scheduler.run_verification", new_callable=AsyncMock)
def test_verify_job_exception_handling(mock_run_verification, mock_session_local):
    """Test verification job handles exceptions."""
    # Setup mocks
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Simulate an exception
    mock_run_verification.side_effect = Exception("Database connection failed")

    # Execute job - should not raise
    _verify_kr_job()

    # Verify cleanup still happens
    mock_db.close.assert_called_once()


def test_register_jobs_replaces_existing():
    """Test that registering jobs replaces existing ones."""
    scheduler = BackgroundScheduler()

    # Register jobs twice
    register_verification_jobs(scheduler)
    register_verification_jobs(scheduler)

    # With replace_existing=True, we should have unique job IDs
    # APScheduler keeps the same job IDs but updates the job
    jobs = scheduler.get_jobs()
    job_ids = [job.id for job in jobs]

    # Should have exactly 2 unique job IDs
    assert len(set(job_ids)) == 2
    assert "kr_verification" in job_ids
    assert "us_verification" in job_ids
