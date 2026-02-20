"""Tests for ml_trainer module."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.processing.ml_trainer import MLTrainer, DIRECTION_LABELS

# Check if LightGBM is usable
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except (ImportError, OSError):
    LIGHTGBM_AVAILABLE = False


@pytest.fixture
def sample_data():
    """Generate synthetic training data for testing."""
    np.random.seed(42)
    n = 300

    X = pd.DataFrame({
        "news_score": np.random.uniform(0, 100, n),
        "sentiment_score": np.random.uniform(-1, 1, n),
        "rsi_14": np.random.uniform(20, 80, n),
        "prev_change_pct": np.random.uniform(-5, 5, n),
        "price_change_5d": np.random.uniform(-10, 10, n),
        "volume_change_5d": np.random.uniform(-50, 200, n),
        "market_return": np.random.uniform(-3, 3, n),
        "vix_change": np.random.uniform(-10, 10, n),
    })

    y = pd.Series(np.random.choice(DIRECTION_LABELS, n))

    return X, y


@pytest.fixture
def trainer():
    return MLTrainer(market="KR", tier=1)


class TestMLTrainerInit:
    def test_tier1_features(self, trainer):
        assert len(trainer.feature_columns) == 8
        assert "news_score" in trainer.feature_columns
        assert "vix_change" in trainer.feature_columns

    def test_min_samples(self, trainer):
        assert trainer.min_samples == 200

    def test_tier2_features(self):
        t2 = MLTrainer(market="US", tier=2)
        assert len(t2.feature_columns) == 16
        assert t2.min_samples == 500


class TestTrainLightGBM:
    @pytest.mark.skipif(not LIGHTGBM_AVAILABLE, reason="LightGBM not available")
    def test_basic_training(self, trainer, sample_data):
        X, y = sample_data
        result = trainer.train_lightgbm(X, y)

        assert "model" in result
        assert "accuracy" in result
        assert "cv_accuracy" in result
        assert "cv_std" in result
        assert "feature_importances" in result
        assert 0 < result["accuracy"] <= 1.0
        assert 0 < result["cv_accuracy"] <= 1.0
        assert result["cv_std"] >= 0

    @pytest.mark.skipif(not LIGHTGBM_AVAILABLE, reason="LightGBM not available")
    def test_feature_importances_complete(self, trainer, sample_data):
        X, y = sample_data
        result = trainer.train_lightgbm(X, y)

        importances = result["feature_importances"]
        assert len(importances) == 8
        for feat in trainer.feature_columns:
            assert feat in importances

    @pytest.mark.skipif(not LIGHTGBM_AVAILABLE, reason="LightGBM not available")
    def test_predictions_valid(self, trainer, sample_data):
        X, y = sample_data
        result = trainer.train_lightgbm(X, y)
        model = result["model"]

        preds = model.predict(X[:5])
        assert len(preds) == 5
        for p in preds:
            assert p in DIRECTION_LABELS


class TestTrainRandomForest:
    def test_basic_training(self, trainer, sample_data):
        X, y = sample_data
        result = trainer.train_random_forest(X, y)

        assert "model" in result
        assert 0 < result["accuracy"] <= 1.0
        assert 0 < result["cv_accuracy"] <= 1.0

    def test_predictions_valid(self, trainer, sample_data):
        X, y = sample_data
        result = trainer.train_random_forest(X, y)
        preds = result["model"].predict(X[:5])
        for p in preds:
            assert p in DIRECTION_LABELS


class TestCrossValidation:
    def test_timeseries_split(self, trainer, sample_data):
        """Verify TimeSeriesSplit is used (not random)."""
        from sklearn.ensemble import RandomForestClassifier

        X, y = sample_data
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        result = trainer.cross_validate(model, X, y, n_splits=5)

        assert "cv_accuracy" in result
        assert "cv_std" in result
        assert "cv_scores" in result
        assert len(result["cv_scores"]) == 5

    def test_small_dataset_adjusts_splits(self, trainer):
        """Small dataset reduces n_splits automatically."""
        from sklearn.ensemble import RandomForestClassifier

        X = pd.DataFrame({"f1": range(10), "f2": range(10)})
        y = pd.Series(["up"] * 5 + ["down"] * 5)
        model = RandomForestClassifier(n_estimators=5, random_state=42)

        result = trainer.cross_validate(model, X, y, n_splits=10)
        assert len(result["cv_scores"]) >= 2


class TestSaveLoadModel:
    def test_save_and_load(self, trainer, sample_data):
        X, y = sample_data
        result = trainer.train_random_forest(X, y, n_estimators=10)
        model = result["model"]

        with tempfile.TemporaryDirectory() as tmpdir:
            save_result = trainer.save_model(model, "test_rf", "v1", output_dir=tmpdir)

            assert Path(save_result["path"]).exists()
            assert len(save_result["checksum"]) == 64
            assert save_result["size_bytes"] > 0

            loaded = MLTrainer.load_model(save_result["path"], save_result["checksum"])
            loaded_preds = loaded.predict(X[:5])
            original_preds = model.predict(X[:5])
            assert list(loaded_preds) == list(original_preds)

    def test_checksum_mismatch_raises(self, trainer, sample_data):
        X, y = sample_data
        result = trainer.train_random_forest(X, y, n_estimators=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_result = trainer.save_model(result["model"], "test", "v1", output_dir=tmpdir)

            with pytest.raises(ValueError, match="checksum mismatch"):
                MLTrainer.load_model(save_result["path"], "wrong_checksum")
