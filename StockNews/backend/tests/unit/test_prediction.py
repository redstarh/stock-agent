"""뉴스 기반 주가 예측 모델 테스트."""

import pytest
import numpy as np
from app.processing.prediction import NewsPredictionModel, run_backtest


def _generate_synthetic_data(n_samples: int = 200) -> tuple[list[list[float]], list[str]]:
    """테스트용 합성 데이터 생성.

    명확한 신호 패턴:
    - news_score > 70 AND sentiment_score > 0.5 → "up"
    - news_score < 40 AND sentiment_score < -0.3 → "down"
    - Otherwise → "neutral"

    15% 노이즈 추가.
    """
    np.random.seed(42)
    features = []
    labels = []

    for _ in range(n_samples):
        news_score = np.random.uniform(20, 90)
        sentiment_score = np.random.uniform(-1.0, 1.0)
        news_count = np.random.randint(1, 10)
        avg_score_3d = np.random.uniform(40, 80)

        # 패턴 기반 라벨 생성
        if news_score > 70 and sentiment_score > 0.5:
            label = "up"
        elif news_score < 40 and sentiment_score < -0.3:
            label = "down"
        else:
            label = "neutral"

        # 15% 노이즈 (라벨 랜덤 변경)
        if np.random.random() < 0.15:
            label = np.random.choice(["up", "down", "neutral"])

        features.append([news_score, sentiment_score, float(news_count), avg_score_3d])
        labels.append(label)

    return features, labels


class TestNewsPredictionModel:
    """NewsPredictionModel 단위 테스트."""

    def test_train_returns_metrics(self):
        """학습 후 accuracy, std, n_samples 반환."""
        model = NewsPredictionModel()
        features, labels = _generate_synthetic_data(100)

        metrics = model.train(features, labels)

        assert "accuracy" in metrics
        assert "std" in metrics
        assert "n_samples" in metrics
        assert metrics["n_samples"] == 100
        assert 0.0 <= metrics["accuracy"] <= 1.0
        assert metrics["std"] >= 0.0

    def test_predict_returns_direction_and_confidence(self):
        """예측 결과에 direction과 confidence 포함."""
        model = NewsPredictionModel()
        features, labels = _generate_synthetic_data(50)

        model.train(features, labels)
        predictions = model.predict(features[:5])

        assert len(predictions) == 5
        for pred in predictions:
            assert "direction" in pred
            assert "confidence" in pred
            assert pred["direction"] in ["up", "down", "neutral"]
            assert 0.0 <= pred["confidence"] <= 1.0

    def test_predict_single(self):
        """단일 종목 예측."""
        model = NewsPredictionModel()
        features, labels = _generate_synthetic_data(50)

        model.train(features, labels)
        prediction = model.predict_single(
            news_score=75.0,
            sentiment_score=0.6,
            news_count=3,
            avg_score_3d=70.0,
        )

        assert "direction" in prediction
        assert "confidence" in prediction
        assert prediction["direction"] in ["up", "down", "neutral"]

    def test_predict_before_train_raises(self):
        """학습 전 예측 시 RuntimeError."""
        model = NewsPredictionModel()

        with pytest.raises(RuntimeError, match="Model not trained"):
            model.predict([[70.0, 0.5, 3.0, 65.0]])

    def test_prediction_score_range(self):
        """confidence 0.0~1.0 범위."""
        model = NewsPredictionModel()
        features, labels = _generate_synthetic_data(50)

        model.train(features, labels)
        predictions = model.predict(features[:10])

        for pred in predictions:
            assert 0.0 <= pred["confidence"] <= 1.0

    def test_direction_values(self):
        """direction이 up/down/neutral 중 하나."""
        model = NewsPredictionModel()
        features, labels = _generate_synthetic_data(50)

        model.train(features, labels)
        predictions = model.predict(features[:10])

        valid_directions = {"up", "down", "neutral"}
        for pred in predictions:
            assert pred["direction"] in valid_directions

    def test_is_trained_property(self):
        """is_trained 프로퍼티 동작 확인."""
        model = NewsPredictionModel()
        assert not model.is_trained

        features, labels = _generate_synthetic_data(50)
        model.train(features, labels)

        assert model.is_trained


class TestBacktest:
    """run_backtest 함수 테스트."""

    def test_backtest_accuracy_above_60_percent(self):
        """백테스트 정확도 60%+ (synthetic data with clear signal)."""
        features, labels = _generate_synthetic_data(200)
        model = NewsPredictionModel()

        results = run_backtest(model, features, labels, train_ratio=0.7)

        assert results["accuracy"] >= 0.60, f"Accuracy {results['accuracy']:.2%} < 60%"

    def test_backtest_correlation_above_03(self):
        """상관계수 0.3+ (synthetic data with clear signal)."""
        features, labels = _generate_synthetic_data(200)
        model = NewsPredictionModel()

        results = run_backtest(model, features, labels, train_ratio=0.7)

        assert results["correlation"] >= 0.30, f"Correlation {results['correlation']:.2f} < 0.3"

    def test_backtest_split_ratio(self):
        """train/test 7:3 분할 검증."""
        features, labels = _generate_synthetic_data(100)
        model = NewsPredictionModel()

        results = run_backtest(model, features, labels, train_ratio=0.7)

        assert results["n_train"] == 70
        assert results["n_test"] == 30

    def test_backtest_returns_predictions(self):
        """백테스트 결과에 predictions 포함."""
        features, labels = _generate_synthetic_data(50)
        model = NewsPredictionModel()

        results = run_backtest(model, features, labels, train_ratio=0.7)

        assert "predictions" in results
        assert len(results["predictions"]) == results["n_test"]

        for pred in results["predictions"]:
            assert "direction" in pred
            assert "confidence" in pred

    def test_backtest_model_is_trained_after(self):
        """백테스트 후 모델이 학습된 상태."""
        features, labels = _generate_synthetic_data(50)
        model = NewsPredictionModel()

        assert not model.is_trained

        run_backtest(model, features, labels, train_ratio=0.7)

        assert model.is_trained

    def test_backtest_with_different_ratios(self):
        """다양한 train_ratio 값 검증."""
        features, labels = _generate_synthetic_data(100)

        for ratio in [0.6, 0.7, 0.8]:
            model = NewsPredictionModel()
            results = run_backtest(model, features, labels, train_ratio=ratio)

            expected_train = int(100 * ratio)
            expected_test = 100 - expected_train

            assert results["n_train"] == expected_train
            assert results["n_test"] == expected_test
