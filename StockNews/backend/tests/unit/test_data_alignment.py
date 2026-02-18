"""Data alignment module tests (TDD RED phase)."""

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Base
from app.models.stock_price import StockPrice
from app.processing.data_alignment import (
    align_news_and_prices,
    build_feature_dataset,
)


class TestStockPriceModel:
    """StockPrice 모델 테스트."""

    def test_create_stock_price(self, db_session):
        """StockPrice 레코드 생성."""
        price = StockPrice(
            stock_code="005930",
            market="KR",
            date=date(2024, 1, 15),
            close_price=75000.0,
            change_pct=2.5,
            volume=1000000,
        )
        db_session.add(price)
        db_session.commit()
        db_session.refresh(price)

        assert price.id is not None
        assert price.stock_code == "005930"
        assert price.market == "KR"
        assert price.date == date(2024, 1, 15)
        assert price.close_price == 75000.0
        assert price.change_pct == 2.5
        assert price.volume == 1000000
        assert price.created_at is not None

    def test_unique_code_date(self, db_session):
        """같은 stock_code + date는 중복 불가."""
        price1 = StockPrice(
            stock_code="005930",
            market="KR",
            date=date(2024, 1, 15),
            close_price=75000.0,
            change_pct=2.5,
            volume=1000000,
        )
        db_session.add(price1)
        db_session.commit()

        price2 = StockPrice(
            stock_code="005930",
            market="KR",
            date=date(2024, 1, 15),
            close_price=76000.0,
            change_pct=1.3,
            volume=900000,
        )
        db_session.add(price2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestDataAlignment:
    """Data alignment 함수 테스트."""

    @pytest.fixture
    def mock_news_events(self):
        """테스트용 뉴스 이벤트 (dict 형태)."""
        return [
            {
                "stock_code": "005930",
                "news_date": date(2024, 1, 15),
                "news_score": 75.0,
                "sentiment_score": 0.8,
            },
            {
                "stock_code": "005930",
                "news_date": date(2024, 1, 16),
                "news_score": 60.0,
                "sentiment_score": 0.5,
            },
            {
                "stock_code": "000660",
                "news_date": date(2024, 1, 15),
                "news_score": 80.0,
                "sentiment_score": 0.9,
            },
        ]

    @pytest.fixture
    def mock_stock_prices(self):
        """테스트용 주가 데이터 (dict 형태)."""
        return [
            {
                "stock_code": "005930",
                "date": date(2024, 1, 16),
                "change_pct": 2.5,
            },
            {
                "stock_code": "005930",
                "date": date(2024, 1, 17),
                "change_pct": -1.2,
            },
            {
                "stock_code": "000660",
                "date": date(2024, 1, 16),
                "change_pct": 0.3,
            },
        ]

    def test_align_basic(self, mock_news_events, mock_stock_prices):
        """뉴스 날짜 다음 거래일 주가와 매칭."""
        aligned = align_news_and_prices(mock_news_events, mock_stock_prices)

        assert len(aligned) >= 2
        # 첫 번째 뉴스 (2024-01-15) → 다음 거래일 주가 (2024-01-16)
        first = next(
            (a for a in aligned if a["news_date"] == date(2024, 1, 15)), None
        )
        assert first is not None
        assert first["stock_code"] == "005930"
        assert first["price_date"] == date(2024, 1, 16)
        assert first["change_pct"] == 2.5

    def test_align_weekend_skip(self):
        """금요일 뉴스 → 월요일 주가 매칭."""
        news = [
            {
                "stock_code": "005930",
                "news_date": date(2024, 1, 19),  # 금요일
                "news_score": 70.0,
                "sentiment_score": 0.6,
            }
        ]
        prices = [
            {
                "stock_code": "005930",
                "date": date(2024, 1, 22),  # 월요일
                "change_pct": 1.5,
            }
        ]
        aligned = align_news_and_prices(news, prices)

        assert len(aligned) == 1
        assert aligned[0]["news_date"] == date(2024, 1, 19)
        assert aligned[0]["price_date"] == date(2024, 1, 22)
        assert aligned[0]["change_pct"] == 1.5

    def test_align_no_price_data(self, mock_news_events):
        """주가 데이터 없는 뉴스 → 스킵."""
        prices = []
        aligned = align_news_and_prices(mock_news_events, prices)

        assert len(aligned) == 0

    def test_direction_classification(self, mock_news_events, mock_stock_prices):
        """change_pct > 0.5% = up, < -0.5% = down, else neutral."""
        aligned = align_news_and_prices(mock_news_events, mock_stock_prices)

        # change_pct = 2.5% → "up"
        up_item = next((a for a in aligned if a["change_pct"] == 2.5), None)
        assert up_item is not None
        assert up_item["direction"] == "up"

        # change_pct = -1.2% → "down"
        down_item = next((a for a in aligned if a["change_pct"] == -1.2), None)
        assert down_item is not None
        assert down_item["direction"] == "down"

        # change_pct = 0.3% → "neutral"
        neutral_item = next((a for a in aligned if a["change_pct"] == 0.3), None)
        assert neutral_item is not None
        assert neutral_item["direction"] == "neutral"

    def test_build_feature_dataset(self):
        """피처 벡터 + 라벨 생성 검증."""
        aligned_data = [
            {
                "stock_code": "005930",
                "news_date": date(2024, 1, 15),
                "news_score": 75.0,
                "sentiment_score": 0.8,
                "price_date": date(2024, 1, 16),
                "change_pct": 2.5,
                "direction": "up",
            },
            {
                "stock_code": "005930",
                "news_date": date(2024, 1, 16),
                "news_score": 60.0,
                "sentiment_score": 0.5,
                "price_date": date(2024, 1, 17),
                "change_pct": -1.2,
                "direction": "down",
            },
        ]

        features, labels = build_feature_dataset(aligned_data)

        assert len(features) == 2
        assert len(labels) == 2
        assert labels[0] == "up"
        assert labels[1] == "down"

    def test_feature_dimensions(self):
        """피처 벡터 차원 = 4 (news_score, sentiment_score, count, avg_3d)."""
        aligned_data = [
            {
                "stock_code": "005930",
                "news_date": date(2024, 1, 15),
                "news_score": 75.0,
                "sentiment_score": 0.8,
                "price_date": date(2024, 1, 16),
                "change_pct": 2.5,
                "direction": "up",
            }
        ]

        features, labels = build_feature_dataset(aligned_data)

        assert len(features) == 1
        assert len(features[0]) == 4

    def test_nan_ratio_below_10pct(self):
        """NaN 비율 10% 미만."""
        # 30일 주가 데이터 + 50개 뉴스
        base_date = date(2024, 1, 1)
        news_events = []
        stock_prices = []

        # 30일 주가 생성 (주말 제외)
        current_date = base_date
        for i in range(30):
            # 주말 건너뛰기
            while current_date.weekday() >= 5:
                current_date += timedelta(days=1)

            stock_prices.append(
                {
                    "stock_code": "005930",
                    "date": current_date,
                    "change_pct": (i % 10 - 5) * 0.5,  # -2.5% ~ +2.0%
                }
            )
            current_date += timedelta(days=1)

        # 50개 뉴스 (30일 중 랜덤하게 분포)
        import random

        random.seed(42)
        for i in range(50):
            news_date = base_date + timedelta(days=random.randint(0, 29))
            news_events.append(
                {
                    "stock_code": "005930",
                    "news_date": news_date,
                    "news_score": 50.0 + random.random() * 50,
                    "sentiment_score": random.random(),
                }
            )

        aligned = align_news_and_prices(news_events, stock_prices)

        # NaN 비율 계산 (매칭 실패 비율)
        nan_ratio = 1 - (len(aligned) / len(news_events))
        assert nan_ratio < 0.10


@pytest.fixture
def realistic_test_data():
    """현실적인 30일 주가 + 50개 뉴스 데이터."""
    import random

    random.seed(42)

    base_date = date(2024, 1, 1)
    news_events = []
    stock_prices = []

    # 30일 주가 생성 (주말 제외)
    current_date = base_date
    price = 75000.0
    for i in range(30):
        # 주말 건너뛰기
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)

        # 현실적인 주가 변동 (-3% ~ +3%)
        change_pct = (random.random() - 0.5) * 6
        price = price * (1 + change_pct / 100)

        stock_prices.append(
            {
                "stock_code": "005930",
                "date": current_date,
                "change_pct": change_pct,
            }
        )
        current_date += timedelta(days=1)

    # 50개 뉴스 (30일 중 분포)
    for i in range(50):
        news_date = base_date + timedelta(days=random.randint(0, 29))
        news_events.append(
            {
                "stock_code": "005930",
                "news_date": news_date,
                "news_score": 40.0 + random.random() * 60,
                "sentiment_score": random.random() * 2 - 1,  # -1.0 ~ +1.0
            }
        )

    return news_events, stock_prices


def test_realistic_integration(realistic_test_data):
    """현실적인 데이터로 전체 파이프라인 검증."""
    news_events, stock_prices = realistic_test_data

    aligned = align_news_and_prices(news_events, stock_prices)
    assert len(aligned) > 0

    features, labels = build_feature_dataset(aligned)
    assert len(features) == len(labels)
    assert len(features) > 0

    # 각 피처 벡터가 4차원
    for feat in features:
        assert len(feat) == 4

    # 라벨이 up/down/neutral 중 하나
    for label in labels:
        assert label in ["up", "down", "neutral"]
