"""Tests for theme_aggregator.py"""

import pytest
from datetime import date, datetime, timedelta

from app.models.news_event import NewsEvent
from app.models.verification import DailyPredictionResult, ThemePredictionAccuracy
from app.processing.theme_aggregator import aggregate_theme_accuracy


def test_aggregate_empty_results(db_session):
    """Test aggregation with no results returns empty list."""
    target_date = date(2026, 2, 19)

    results = aggregate_theme_accuracy(db_session, target_date, "KR")

    assert results == []


def test_aggregate_single_theme(db_session):
    """Test aggregation for stocks with single theme."""
    target_date = date(2026, 2, 19)

    # Create news events with theme
    news1 = NewsEvent(
        market="KR",
        stock_code="005930",
        stock_name="삼성전자",
        title="반도체 뉴스 1",
        sentiment="positive",
        sentiment_score=0.5,
        news_score=70.0,
        source="test",
        theme="반도체",
        created_at=datetime.combine(target_date, datetime.min.time()),
    )
    news2 = NewsEvent(
        market="KR",
        stock_code="000660",
        stock_name="SK하이닉스",
        title="반도체 뉴스 2",
        sentiment="positive",
        sentiment_score=0.5,
        news_score=70.0,
        source="test",
        theme="반도체",
        created_at=datetime.combine(target_date, datetime.min.time()),
    )
    db_session.add_all([news1, news2])

    # Create prediction results
    result1 = DailyPredictionResult(
        prediction_date=target_date,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        predicted_direction="up",
        predicted_score=72.0,
        confidence=0.8,
        news_count=5,
        actual_direction="up",
        actual_change_pct=2.5,
        is_correct=True,
    )
    result2 = DailyPredictionResult(
        prediction_date=target_date,
        stock_code="000660",
        stock_name="SK하이닉스",
        market="KR",
        predicted_direction="up",
        predicted_score=68.0,
        confidence=0.7,
        news_count=4,
        actual_direction="up",
        actual_change_pct=1.8,
        is_correct=True,
    )
    db_session.add_all([result1, result2])
    db_session.commit()

    results = aggregate_theme_accuracy(db_session, target_date, "KR")

    assert len(results) == 1
    assert results[0].theme == "반도체"
    assert results[0].total_stocks == 2
    assert results[0].correct_count == 2
    assert results[0].accuracy_rate == 1.0
    assert results[0].avg_predicted_score == 70.0
    assert results[0].avg_actual_change_pct == 2.15


def test_aggregate_multiple_themes(db_session):
    """Test aggregation for stocks across different themes."""
    target_date = date(2026, 2, 19)

    # Theme 1: 반도체
    news1 = NewsEvent(
        market="KR",
        stock_code="005930",
        stock_name="삼성전자",
        title="반도체",
        sentiment="positive",
        sentiment_score=0.5,
        news_score=70.0,
        source="test",
        theme="반도체",
        created_at=datetime.combine(target_date, datetime.min.time()),
    )
    result1 = DailyPredictionResult(
        prediction_date=target_date,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        predicted_direction="up",
        predicted_score=72.0,
        confidence=0.8,
        news_count=5,
        actual_direction="up",
        is_correct=True,
    )

    # Theme 2: 자동차
    news2 = NewsEvent(
        market="KR",
        stock_code="005380",
        stock_name="현대차",
        title="자동차",
        sentiment="neutral",
        sentiment_score=0.0,
        news_score=50.0,
        source="test",
        theme="자동차",
        created_at=datetime.combine(target_date, datetime.min.time()),
    )
    result2 = DailyPredictionResult(
        prediction_date=target_date,
        stock_code="005380",
        stock_name="현대차",
        market="KR",
        predicted_direction="neutral",
        predicted_score=50.0,
        confidence=0.5,
        news_count=3,
        actual_direction="down",
        is_correct=False,
    )

    db_session.add_all([news1, news2, result1, result2])
    db_session.commit()

    results = aggregate_theme_accuracy(db_session, target_date, "KR")

    assert len(results) == 2
    themes = {r.theme for r in results}
    assert "반도체" in themes
    assert "자동차" in themes


def test_aggregate_accuracy_calculation(db_session):
    """Test accuracy calculation: 5 correct / 10 total = 0.5"""
    target_date = date(2026, 2, 19)

    # Create 10 stocks with same theme
    for i in range(10):
        stock_code = f"00{i:04d}"
        news = NewsEvent(
            market="KR",
            stock_code=stock_code,
            stock_name=f"종목{i}",
            title=f"AI 뉴스 {i}",
            sentiment="positive",
            sentiment_score=0.5,
            news_score=70.0,
            source="test",
            theme="AI",
            created_at=datetime.combine(target_date, datetime.min.time()),
        )
        result = DailyPredictionResult(
            prediction_date=target_date,
            stock_code=stock_code,
            stock_name=f"종목{i}",
            market="KR",
            predicted_direction="up",
            predicted_score=70.0,
            confidence=0.7,
            news_count=5,
            actual_direction="up" if i < 5 else "down",  # 5 correct, 5 wrong
            is_correct=(i < 5),
        )
        db_session.add(news)
        db_session.add(result)

    db_session.commit()

    results = aggregate_theme_accuracy(db_session, target_date, "KR")

    assert len(results) == 1
    assert results[0].theme == "AI"
    assert results[0].total_stocks == 10
    assert results[0].correct_count == 5
    assert results[0].accuracy_rate == 0.5


def test_aggregate_with_no_theme_news(db_session):
    """Test that stocks with no theme are skipped."""
    target_date = date(2026, 2, 19)

    # Create result but no news with theme
    result = DailyPredictionResult(
        prediction_date=target_date,
        stock_code="999999",
        stock_name="테마없음",
        market="KR",
        predicted_direction="up",
        predicted_score=70.0,
        confidence=0.7,
        news_count=5,
        actual_direction="up",
        is_correct=True,
    )
    db_session.add(result)
    db_session.commit()

    results = aggregate_theme_accuracy(db_session, target_date, "KR")

    assert results == []


def test_aggregate_comma_separated_themes(db_session):
    """Test that comma-separated themes are counted in both."""
    target_date = date(2026, 2, 19)

    # News with multiple themes
    news = NewsEvent(
        market="KR",
        stock_code="005930",
        stock_name="삼성전자",
        title="반도체 AI 뉴스",
        sentiment="positive",
        sentiment_score=0.5,
        news_score=70.0,
        source="test",
        theme="반도체,AI",  # Multiple themes
        created_at=datetime.combine(target_date, datetime.min.time()),
    )
    result = DailyPredictionResult(
        prediction_date=target_date,
        stock_code="005930",
        stock_name="삼성전자",
        market="KR",
        predicted_direction="up",
        predicted_score=72.0,
        confidence=0.8,
        news_count=5,
        actual_direction="up",
        actual_change_pct=2.5,
        is_correct=True,
    )
    db_session.add(news)
    db_session.add(result)
    db_session.commit()

    results = aggregate_theme_accuracy(db_session, target_date, "KR")

    # Should create entries for both themes
    assert len(results) == 2
    themes = {r.theme for r in results}
    assert "반도체" in themes
    assert "AI" in themes

    # Both should reference the same stock
    for r in results:
        assert r.total_stocks == 1
        assert r.correct_count == 1
        assert r.accuracy_rate == 1.0
