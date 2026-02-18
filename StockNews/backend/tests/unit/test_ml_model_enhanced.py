"""Tests for enhanced ml_model module."""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.processing.ml_model import (
    EnhancedPredictionModel,
    train_model_from_db,
)


@pytest.fixture
def sample_training_data():
    """샘플 학습 데이터."""
    features = [
        [70.0, 0.5, 20.0, 75.0, 0.3, 5.0, 15.0, 1.05],  # up
        [65.0, 0.3, 18.0, 68.0, 0.25, 3.5, 12.0, 1.03],  # up
        [40.0, -0.3, 10.0, 35.0, 0.1, -4.0, -10.0, 0.95],  # down
        [45.0, -0.2, 12.0, 42.0, 0.15, -3.5, -8.0, 0.96],  # down
        [55.0, 0.1, 15.0, 55.0, 0.2, 0.5, 5.0, 1.0],  # neutral
        [58.0, 0.0, 16.0, 57.0, 0.18, 1.0, 3.0, 1.01],  # neutral
    ]
    labels = ["up", "up", "down", "down", "neutral", "neutral"]
    return features, labels


class TestEnhancedPredictionModel:
    """EnhancedPredictionModel 테스트."""

    def test_model_initialization(self):
        """모델 초기화."""
        model = EnhancedPredictionModel()

        assert not model.is_trained
        assert model.model is not None
        assert model.scaler is not None

    def test_train_success(self, sample_training_data):
        """모델 학습 성공."""
        features, labels = sample_training_data
        model = EnhancedPredictionModel()

        metrics = model.train(features, labels)

        assert model.is_trained
        assert "accuracy" in metrics
        assert "std" in metrics
        assert "n_samples" in metrics
        assert "cv_folds" in metrics
        assert metrics["n_samples"] == 6
        assert 0 <= metrics["accuracy"] <= 1

    def test_train_insufficient_samples(self):
        """샘플 부족 시 에러."""
        model = EnhancedPredictionModel()
        features = [[1, 2, 3, 4, 5, 6, 7, 8]]
        labels = ["up"]

        with pytest.raises(ValueError, match="Need at least 5 samples"):
            model.train(features, labels)

    def test_predict_success(self, sample_training_data):
        """예측 성공."""
        features, labels = sample_training_data
        model = EnhancedPredictionModel()
        model.train(features, labels)

        # 새로운 데이터 예측
        test_features = [
            [68.0, 0.4, 19.0, 70.0, 0.28, 4.5, 13.0, 1.04],
        ]
        predictions = model.predict(test_features)

        assert len(predictions) == 1
        assert "direction" in predictions[0]
        assert "confidence" in predictions[0]
        assert predictions[0]["direction"] in ["up", "down", "neutral"]
        assert 0 <= predictions[0]["confidence"] <= 1

    def test_predict_untrained_model(self):
        """학습되지 않은 모델 예측 시 에러."""
        model = EnhancedPredictionModel()
        test_features = [[1, 2, 3, 4, 5, 6, 7, 8]]

        with pytest.raises(RuntimeError, match="Model not trained"):
            model.predict(test_features)

    @patch("app.processing.ml_model.build_feature_vector")
    def test_predict_direction(self, mock_build, sample_training_data):
        """종목 방향 예측."""
        features, labels = sample_training_data
        model = EnhancedPredictionModel()
        model.train(features, labels)

        mock_build.return_value = {
            "news_score": 70.0,
            "sentiment_score": 0.5,
            "news_count": 20,
            "avg_score_3d": 75.0,
            "disclosure_ratio": 0.3,
            "price_change_pct": 5.0,
            "volume_change_pct": 15.0,
            "moving_average_ratio": 1.05,
        }

        mock_db = Mock(spec=Session)
        result = model.predict_direction("005930", mock_db)

        assert "direction" in result
        assert "confidence" in result
        assert result["direction"] in ["up", "down", "neutral"]

    @patch("app.processing.ml_model.build_feature_vector")
    def test_predict_direction_untrained(self, mock_build):
        """학습되지 않은 모델로 predict_direction 호출."""
        model = EnhancedPredictionModel()
        mock_db = Mock(spec=Session)

        with pytest.raises(RuntimeError, match="Model not trained"):
            model.predict_direction("005930", mock_db)

    @patch("app.processing.ml_model.build_feature_vector")
    def test_backtest(self, mock_build, sample_training_data):
        """백테스트."""
        features, labels = sample_training_data
        model = EnhancedPredictionModel()
        model.train(features, labels)

        mock_build.return_value = {
            "news_score": 70.0,
            "sentiment_score": 0.5,
            "news_count": 20,
            "avg_score_3d": 75.0,
            "disclosure_ratio": 0.3,
            "price_change_pct": 5.0,  # actual: up
            "volume_change_pct": 15.0,
            "moving_average_ratio": 1.05,
        }

        mock_db = Mock(spec=Session)
        result = model.backtest("005930", mock_db, test_days=30)

        assert "accuracy" in result
        assert "predictions" in result
        assert 0 <= result["accuracy"] <= 1
        assert len(result["predictions"]) > 0
        assert "predicted" in result["predictions"][0]
        assert "actual" in result["predictions"][0]
        assert "confidence" in result["predictions"][0]

    def test_save_and_load_model(self, sample_training_data):
        """모델 저장 및 로드."""
        features, labels = sample_training_data
        model = EnhancedPredictionModel()
        model.train(features, labels)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_model.pkl")

            # 저장
            model.save_model(filepath)
            assert os.path.exists(filepath)

            # 로드
            new_model = EnhancedPredictionModel()
            assert not new_model.is_trained

            new_model.load_model(filepath)
            assert new_model.is_trained

            # 예측 가능한지 확인
            test_features = [[68.0, 0.4, 19.0, 70.0, 0.28, 4.5, 13.0, 1.04]]
            predictions = new_model.predict(test_features)
            assert len(predictions) == 1

    def test_save_untrained_model(self):
        """학습되지 않은 모델 저장 시 에러."""
        model = EnhancedPredictionModel()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_model.pkl")
            with pytest.raises(RuntimeError, match="Cannot save untrained model"):
                model.save_model(filepath)

    def test_load_nonexistent_model(self):
        """존재하지 않는 모델 로드 시 에러."""
        model = EnhancedPredictionModel()

        with pytest.raises(FileNotFoundError):
            model.load_model("/nonexistent/path/model.pkl")


class TestTrainModelFromDb:
    """train_model_from_db 테스트."""

    @patch("app.processing.ml_model.prepare_training_data")
    def test_train_model_from_db(self, mock_prepare):
        """DB에서 모델 학습."""
        mock_prepare.return_value = (
            [
                [70.0, 0.5, 20.0, 75.0, 0.3, 5.0, 15.0, 1.05],
                [65.0, 0.3, 18.0, 68.0, 0.25, 3.5, 12.0, 1.03],
                [40.0, -0.3, 10.0, 35.0, 0.1, -4.0, -10.0, 0.95],
                [45.0, -0.2, 12.0, 42.0, 0.15, -3.5, -8.0, 0.96],
                [55.0, 0.1, 15.0, 55.0, 0.2, 0.5, 5.0, 1.0],
                [58.0, 0.0, 16.0, 57.0, 0.18, 1.0, 3.0, 1.01],
            ],
            ["up", "up", "down", "down", "neutral", "neutral"],
            ["005930", "035720", "AAPL", "TSLA", "MSFT", "GOOGL"],
        )

        mock_db = Mock(spec=Session)
        stock_codes = ["005930", "035720", "AAPL"]

        model, metrics = train_model_from_db(stock_codes, mock_db)

        assert model.is_trained
        assert "accuracy" in metrics
        assert metrics["n_samples"] == 6


class TestModelPerformance:
    """모델 성능 테스트."""

    def test_model_achieves_reasonable_accuracy(self):
        """모델이 합리적인 정확도 달성."""
        # 명확한 패턴을 가진 데이터 생성
        features = []
        labels = []

        # up 패턴: 높은 news_score, 긍정 sentiment, 높은 price_change
        for _ in range(15):
            features.append([75.0, 0.6, 25.0, 80.0, 0.3, 6.0, 20.0, 1.08])
            labels.append("up")

        # down 패턴: 낮은 news_score, 부정 sentiment, 낮은 price_change
        for _ in range(15):
            features.append([35.0, -0.6, 8.0, 30.0, 0.1, -6.0, -20.0, 0.92])
            labels.append("down")

        # neutral 패턴
        for _ in range(15):
            features.append([50.0, 0.0, 15.0, 50.0, 0.2, 0.0, 0.0, 1.0])
            labels.append("neutral")

        model = EnhancedPredictionModel()
        metrics = model.train(features, labels)

        # 명확한 패턴이 있으므로 60% 이상 정확도 기대
        assert metrics["accuracy"] >= 0.6, f"Accuracy too low: {metrics['accuracy']}"
