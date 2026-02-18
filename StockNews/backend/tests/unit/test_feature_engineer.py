"""Tests for feature_engineer module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from sqlalchemy.orm import Session

from app.models.news_event import NewsEvent
from app.processing.feature_engineer import (
    build_feature_vector,
    extract_news_features,
    extract_price_features,
    prepare_training_data,
)


@pytest.fixture
def sample_news_events():
    """샘플 뉴스 이벤트."""
    now = datetime.now(timezone.utc)
    events = []

    for i in range(10):
        event = NewsEvent(
            id=i + 1,
            market="KR",
            stock_code="005930",
            stock_name="삼성전자",
            title=f"News {i}",
            summary=f"Summary {i}",
            sentiment="positive" if i % 2 == 0 else "negative",
            sentiment_score=0.5 if i % 2 == 0 else -0.5,
            news_score=60 + i,
            source="test",
            is_disclosure=i % 3 == 0,
            published_at=now - timedelta(days=i),
            created_at=now - timedelta(days=i),
        )
        events.append(event)

    return events


class TestExtractNewsFeatures:
    """extract_news_features 테스트."""

    def test_extract_news_features_normal(self, sample_news_events):
        """정상 케이스."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_news_events
        mock_db.query.return_value = mock_query

        features = extract_news_features("005930", mock_db, days=30)

        assert "news_score" in features
        assert "sentiment_score" in features
        assert "news_count" in features
        assert "avg_score_3d" in features
        assert "disclosure_ratio" in features

        assert features["news_count"] == 10
        assert 0 <= features["news_score"] <= 100
        assert -1 <= features["sentiment_score"] <= 1
        assert 0 <= features["disclosure_ratio"] <= 1

    def test_extract_news_features_no_news(self):
        """뉴스가 없는 경우."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        features = extract_news_features("INVALID", mock_db)

        assert features["news_score"] == 0.0
        assert features["sentiment_score"] == 0.0
        assert features["news_count"] == 0
        assert features["avg_score_3d"] == 0.0
        assert features["disclosure_ratio"] == 0.0

    def test_extract_news_features_disclosure_ratio(self, sample_news_events):
        """공시 비율 계산."""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_news_events
        mock_db.query.return_value = mock_query

        features = extract_news_features("005930", mock_db)

        # 10개 중 4개가 공시 (i=0,3,6,9)
        expected_ratio = 4 / 10
        assert features["disclosure_ratio"] == pytest.approx(expected_ratio, rel=0.01)


class TestExtractPriceFeatures:
    """extract_price_features 테스트."""

    @patch("app.processing.feature_engineer.fetch_recent_price_change")
    def test_extract_price_features_normal(self, mock_fetch):
        """정상 케이스."""
        mock_fetch.return_value = {
            "change_pct": 5.2,
            "volume_change_pct": 15.3,
            "ma_ratio": 1.05,
        }

        features = extract_price_features("005930")

        assert features["price_change_pct"] == 5.2
        assert features["volume_change_pct"] == 15.3
        assert features["moving_average_ratio"] == 1.05

    @patch("app.processing.feature_engineer.fetch_recent_price_change")
    def test_extract_price_features_no_data(self, mock_fetch):
        """데이터가 없는 경우."""
        mock_fetch.return_value = {
            "change_pct": 0.0,
            "volume_change_pct": 0.0,
            "ma_ratio": 1.0,
        }

        features = extract_price_features("INVALID")

        assert features["price_change_pct"] == 0.0
        assert features["volume_change_pct"] == 0.0
        assert features["moving_average_ratio"] == 1.0


class TestBuildFeatureVector:
    """build_feature_vector 테스트."""

    @patch("app.processing.feature_engineer.extract_price_features")
    @patch("app.processing.feature_engineer.extract_news_features")
    def test_build_feature_vector(self, mock_news, mock_price):
        """피처 벡터 생성."""
        mock_news.return_value = {
            "news_score": 65.0,
            "sentiment_score": 0.3,
            "news_count": 15,
            "avg_score_3d": 70.0,
            "disclosure_ratio": 0.2,
        }
        mock_price.return_value = {
            "price_change_pct": 3.5,
            "volume_change_pct": 10.0,
            "moving_average_ratio": 1.02,
        }

        mock_db = Mock(spec=Session)
        features = build_feature_vector("005930", mock_db)

        assert len(features) == 8
        assert features["news_score"] == 65.0
        assert features["sentiment_score"] == 0.3
        assert features["news_count"] == 15
        assert features["price_change_pct"] == 3.5


class TestPrepareTrainingData:
    """prepare_training_data 테스트."""

    @patch("app.processing.feature_engineer.build_feature_vector")
    def test_prepare_training_data_normal(self, mock_build):
        """정상 케이스."""
        mock_build.side_effect = [
            {
                "news_score": 70.0,
                "sentiment_score": 0.5,
                "news_count": 20,
                "avg_score_3d": 75.0,
                "disclosure_ratio": 0.3,
                "price_change_pct": 5.0,  # → up
                "volume_change_pct": 15.0,
                "moving_average_ratio": 1.05,
            },
            {
                "news_score": 40.0,
                "sentiment_score": -0.3,
                "news_count": 10,
                "avg_score_3d": 35.0,
                "disclosure_ratio": 0.1,
                "price_change_pct": -4.0,  # → down
                "volume_change_pct": -10.0,
                "moving_average_ratio": 0.95,
            },
            {
                "news_score": 55.0,
                "sentiment_score": 0.1,
                "news_count": 15,
                "avg_score_3d": 55.0,
                "disclosure_ratio": 0.2,
                "price_change_pct": 0.5,  # → neutral
                "volume_change_pct": 5.0,
                "moving_average_ratio": 1.0,
            },
        ]

        mock_db = Mock(spec=Session)
        stock_codes = ["005930", "035720", "AAPL"]

        features, labels, codes = prepare_training_data(stock_codes, mock_db)

        assert len(features) == 3
        assert len(labels) == 3
        assert len(codes) == 3

        assert len(features[0]) == 8  # 8 features per sample
        assert labels[0] == "up"
        assert labels[1] == "down"
        assert labels[2] == "neutral"

        assert codes == stock_codes

    @patch("app.processing.feature_engineer.build_feature_vector")
    def test_prepare_training_data_label_generation(self, mock_build):
        """레이블 생성 로직 확인."""
        mock_build.side_effect = [
            {
                "news_score": 60.0,
                "sentiment_score": 0.2,
                "news_count": 12,
                "avg_score_3d": 62.0,
                "disclosure_ratio": 0.15,
                "price_change_pct": 2.5,  # > 2.0 → up
                "volume_change_pct": 8.0,
                "moving_average_ratio": 1.02,
            },
            {
                "news_score": 50.0,
                "sentiment_score": -0.1,
                "news_count": 8,
                "avg_score_3d": 48.0,
                "disclosure_ratio": 0.1,
                "price_change_pct": -2.5,  # < -2.0 → down
                "volume_change_pct": -5.0,
                "moving_average_ratio": 0.98,
            },
            {
                "news_score": 55.0,
                "sentiment_score": 0.0,
                "news_count": 10,
                "avg_score_3d": 55.0,
                "disclosure_ratio": 0.2,
                "price_change_pct": 1.0,  # -2.0 <= x <= 2.0 → neutral
                "volume_change_pct": 3.0,
                "moving_average_ratio": 1.0,
            },
        ]

        mock_db = Mock(spec=Session)
        features, labels, codes = prepare_training_data(["A", "B", "C"], mock_db)

        assert labels == ["up", "down", "neutral"]
