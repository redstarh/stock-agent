"""Prediction Context Builder 단위 테스트."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.training import StockTrainingData
from app.models.verification import DailyPredictionResult, ThemePredictionAccuracy
from app.processing.prediction_context_builder import (
    build_prediction_context,
    build_and_save_prediction_context,
    _analyze_direction_accuracy,
    _analyze_news_count_effect,
    _analyze_confidence_calibration,
    _analyze_score_ranges,
    _analyze_failure_patterns,
)


@pytest.fixture
def sample_verified_results(db_session):
    """검증 완료된 예측 결과 시딩."""
    today = date.today()
    now = datetime.now(timezone.utc)
    results = [
        # Correct up prediction, high score
        DailyPredictionResult(
            prediction_date=today,
            stock_code="005930",
            stock_name="삼성전자",
            market="KR",
            predicted_direction="up",
            predicted_score=75.0,
            confidence=0.8,
            news_count=12,
            actual_direction="up",
            actual_change_pct=2.5,
            is_correct=True,
            verified_at=now,
        ),
        # Correct down prediction
        DailyPredictionResult(
            prediction_date=today,
            stock_code="000660",
            stock_name="SK하이닉스",
            market="KR",
            predicted_direction="down",
            predicted_score=25.0,
            confidence=0.7,
            news_count=8,
            actual_direction="down",
            actual_change_pct=-1.5,
            is_correct=True,
            verified_at=now,
        ),
        # Wrong up prediction (high score but down)
        DailyPredictionResult(
            prediction_date=today,
            stock_code="035420",
            stock_name="NAVER",
            market="KR",
            predicted_direction="up",
            predicted_score=72.0,
            confidence=0.75,
            news_count=3,
            actual_direction="down",
            actual_change_pct=-2.0,
            is_correct=False,
            verified_at=now,
        ),
        # Wrong neutral prediction with big move
        DailyPredictionResult(
            prediction_date=today,
            stock_code="AAPL",
            stock_name="Apple",
            market="US",
            predicted_direction="neutral",
            predicted_score=50.0,
            confidence=0.3,
            news_count=2,
            actual_direction="up",
            actual_change_pct=4.5,
            is_correct=False,
            verified_at=now,
        ),
        # Correct US prediction
        DailyPredictionResult(
            prediction_date=today,
            stock_code="MSFT",
            stock_name="Microsoft",
            market="US",
            predicted_direction="up",
            predicted_score=68.0,
            confidence=0.65,
            news_count=15,
            actual_direction="up",
            actual_change_pct=1.2,
            is_correct=True,
            verified_at=now,
        ),
    ]
    for r in results:
        db_session.add(r)
    db_session.flush()
    return results


@pytest.fixture
def sample_theme_accuracy(db_session):
    """테마별 정확도 시딩."""
    today = date.today()
    now = datetime.now(timezone.utc)
    themes = [
        ThemePredictionAccuracy(
            prediction_date=today,
            theme="반도체",
            market="KR",
            total_stocks=10,
            correct_count=7,
            accuracy_rate=0.7,
            created_at=now,
        ),
        ThemePredictionAccuracy(
            prediction_date=today,
            theme="바이오",
            market="KR",
            total_stocks=5,
            correct_count=2,
            accuracy_rate=0.4,
            created_at=now,
        ),
        ThemePredictionAccuracy(
            prediction_date=today,
            theme="AI",
            market="US",
            total_stocks=8,
            correct_count=6,
            accuracy_rate=0.75,
            created_at=now,
        ),
    ]
    for t in themes:
        db_session.add(t)
    db_session.flush()
    return themes


@pytest.fixture
def sample_training_data(db_session):
    """학습 데이터 시딩."""
    today = date.today()
    now = datetime.now(timezone.utc)
    data = [
        StockTrainingData(
            prediction_date=today,
            stock_code="005930",
            stock_name="삼성전자",
            market="KR",
            sentiment_score=0.7,
            news_count=12,
            theme="반도체",
            predicted_direction="up",
            predicted_score=75.0,
            confidence=0.8,
            actual_direction="up",
            is_correct=True,
            news_score=80.0,
            news_count_3d=30,
            avg_score_3d=78.0,
            disclosure_ratio=0.1,
            sentiment_trend=0.05,
            day_of_week=today.weekday(),
            created_at=now,
        ),
        StockTrainingData(
            prediction_date=today,
            stock_code="000660",
            stock_name="SK하이닉스",
            market="KR",
            sentiment_score=-0.6,
            news_count=8,
            theme="반도체",
            predicted_direction="down",
            predicted_score=25.0,
            confidence=0.7,
            actual_direction="down",
            is_correct=True,
            news_score=30.0,
            news_count_3d=20,
            avg_score_3d=32.0,
            disclosure_ratio=0.0,
            sentiment_trend=-0.1,
            day_of_week=today.weekday(),
            created_at=now,
        ),
        StockTrainingData(
            prediction_date=today,
            stock_code="035420",
            stock_name="NAVER",
            market="KR",
            sentiment_score=0.3,
            news_count=3,
            theme="IT",
            predicted_direction="up",
            predicted_score=72.0,
            confidence=0.75,
            actual_direction="down",
            is_correct=False,
            news_score=70.0,
            news_count_3d=8,
            avg_score_3d=68.0,
            disclosure_ratio=0.0,
            sentiment_trend=0.02,
            day_of_week=today.weekday(),
            created_at=now,
        ),
    ]
    for d in data:
        db_session.add(d)
    db_session.flush()
    return data


class TestBuildPredictionContext:
    """build_prediction_context 테스트."""

    def test_empty_data(self, db_session):
        """빈 데이터로 컨텍스트 생성."""
        ctx = build_prediction_context(db_session, days=30)
        assert ctx["total_predictions"] == 0
        assert ctx["overall_accuracy"] == 0.0
        assert ctx["direction_accuracy"] == []
        assert ctx["failure_patterns"] == []
        assert "version" in ctx
        assert "generated_at" in ctx

    def test_with_data(self, db_session, sample_verified_results, sample_theme_accuracy, sample_training_data):
        """데이터가 있을 때 컨텍스트 생성."""
        ctx = build_prediction_context(db_session, days=30)
        assert ctx["total_predictions"] == 5
        assert ctx["overall_accuracy"] == 60.0  # 3/5 correct
        assert ctx["analysis_days"] == 30
        assert len(ctx["direction_accuracy"]) > 0
        assert len(ctx["theme_predictability"]) > 0

    def test_market_filter(self, db_session, sample_verified_results, sample_theme_accuracy):
        """시장 필터 적용."""
        ctx = build_prediction_context(db_session, days=30, market="KR")
        # Only KR results (005930, 000660, 035420) = 3
        assert ctx["total_predictions"] == 3

    def test_days_filter(self, db_session):
        """기간 필터 — 범위 밖 데이터 제외."""
        old_date = date.today() - timedelta(days=60)
        now = datetime.now(timezone.utc)
        db_session.add(DailyPredictionResult(
            prediction_date=old_date,
            stock_code="005930",
            stock_name="삼성전자",
            market="KR",
            predicted_direction="up",
            predicted_score=70.0,
            confidence=0.5,
            news_count=5,
            actual_direction="up",
            is_correct=True,
            verified_at=now,
        ))
        db_session.flush()

        ctx = build_prediction_context(db_session, days=30)
        assert ctx["total_predictions"] == 0  # 60 days ago, outside 30-day window


class TestDirectionAccuracy:
    """방향별 정확도 분석 테스트."""

    def test_direction_accuracy(self, sample_verified_results):
        """방향별 정확도 계산."""
        result = _analyze_direction_accuracy(sample_verified_results)
        directions = {r["direction"]: r for r in result}

        assert "up" in directions
        assert "down" in directions
        assert "neutral" in directions

        # up: 2 correct out of 3 (005930, MSFT correct; NAVER wrong)
        assert directions["up"]["total"] == 3
        assert directions["up"]["correct"] == 2
        assert directions["up"]["accuracy"] == pytest.approx(66.7, abs=0.1)

        # down: 1 correct out of 1
        assert directions["down"]["total"] == 1
        assert directions["down"]["correct"] == 1
        assert directions["down"]["accuracy"] == 100.0


class TestNewsCountEffect:
    """뉴스 건수별 정확도 테스트."""

    def test_news_count_buckets(self, sample_verified_results):
        """뉴스 건수 구간별 정확도."""
        result = _analyze_news_count_effect(sample_verified_results)
        buckets = {r["range_label"]: r for r in result}

        # 1-5: NAVER(3, wrong), AAPL(2, wrong) = 0% accuracy
        assert buckets["1-5"]["total"] == 2
        assert buckets["1-5"]["accuracy"] == 0.0

        # 6-15: 005930(12, correct), 000660(8, correct), MSFT(15, correct) = 100%
        assert buckets["6-15"]["total"] == 3
        assert buckets["6-15"]["accuracy"] == 100.0


class TestFailurePatterns:
    """실패 패턴 감지 테스트."""

    def test_failure_patterns(self, sample_verified_results):
        """실패 패턴 감지."""
        patterns = _analyze_failure_patterns(sample_verified_results)
        pattern_names = {p["pattern"] for p in patterns}

        # NAVER: score 72 but down → high_score_down
        assert "high_score_down" in pattern_names

        # AAPL: neutral prediction but 4.5% move → neutral_big_move
        assert "neutral_big_move" in pattern_names

        # NAVER: confidence 0.75 but wrong → high_confidence_wrong
        assert "high_confidence_wrong" in pattern_names


class TestConfidenceCalibration:
    """Confidence 보정 테스트."""

    def test_confidence_buckets(self, sample_verified_results):
        """Confidence 구간별 정확도."""
        result = _analyze_confidence_calibration(sample_verified_results)
        buckets = {r["range_label"]: r for r in result}

        # 0.0-0.3: AAPL(0.3 is in next bucket) → actually empty or just edge
        # 0.3-0.6: AAPL(0.3) = 1 wrong = 0%
        assert buckets["0.3-0.6"]["total"] == 1
        assert buckets["0.3-0.6"]["accuracy"] == 0.0

        # 0.6-1.0: 005930(0.8, T), 000660(0.7, T), NAVER(0.75, F), MSFT(0.65, T) = 3/4 = 75%
        assert buckets["0.6-1.0"]["total"] == 4
        assert buckets["0.6-1.0"]["accuracy"] == 75.0


class TestBuildAndSave:
    """JSON 파일 저장 테스트."""

    def test_save_to_file(self, db_session, sample_verified_results, tmp_path):
        """JSON 파일 생성 검증."""
        output = tmp_path / "ctx.json"
        ctx = build_and_save_prediction_context(
            db_session, days=30, output_path=str(output)
        )
        assert output.exists()
        assert ctx["total_predictions"] == 5

        import json
        with open(output) as f:
            saved = json.load(f)
        assert saved["total_predictions"] == 5
        assert "version" in saved
