"""Tests for SHAP feature selection and Optuna hyperparameter tuning."""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from app.processing.ml_trainer import MLTrainer


@pytest.fixture
def sample_data():
    """Generate sample training data."""
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        "news_score": np.random.uniform(30, 90, n),
        "sentiment_score": np.random.uniform(-1, 1, n),
        "rsi_14": np.random.uniform(20, 80, n),
        "prev_change_pct": np.random.uniform(-5, 5, n),
        "price_change_5d": np.random.uniform(-10, 10, n),
        "volume_change_5d": np.random.uniform(-20, 50, n),
        "market_return": np.random.uniform(-3, 3, n),
        "vix_change": np.random.uniform(-5, 5, n),
    })
    y = pd.Series(np.random.choice(["up", "down", "neutral"], n))
    return X, y


@pytest.fixture
def trainer():
    """MLTrainer instance."""
    return MLTrainer(market="KR", tier=1)


class TestSHAPFeatureImportance:
    """SHAP feature importance tests."""

    def test_shap_returns_all_features(self, trainer, sample_data):
        """SHAP returns importance for all features."""
        X, y = sample_data
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)

        result = trainer.shap_feature_importance(model, X)

        assert "feature_importances" in result
        assert "mean_shap_values" in result
        assert len(result["feature_importances"]) == 8
        assert len(result["mean_shap_values"]) == 8

    def test_shap_importances_sorted_descending(self, trainer, sample_data):
        """Feature importances are sorted by importance descending."""
        X, y = sample_data
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)

        result = trainer.shap_feature_importance(model, X)

        importances = result["feature_importances"]
        for i in range(len(importances) - 1):
            assert importances[i]["importance"] >= importances[i + 1]["importance"]

    def test_shap_importances_sum_to_one(self, trainer, sample_data):
        """Normalized importances should sum approximately to 1."""
        X, y = sample_data
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)

        result = trainer.shap_feature_importance(model, X)

        total = sum(f["importance"] for f in result["feature_importances"])
        # After rounding to 4 decimals, sum may drift from 1.0
        assert 0.95 <= total <= 1.05  # Allow rounding error

    def test_shap_with_lightgbm(self, trainer, sample_data):
        """SHAP works with LightGBM model."""
        X, y = sample_data
        try:
            import lightgbm as lgb
            model = lgb.LGBMClassifier(n_estimators=10, random_state=42, verbose=-1)
            model.fit(X, y)

            result = trainer.shap_feature_importance(model, X)
            assert len(result["feature_importances"]) == 8
        except ImportError:
            pytest.skip("lightgbm not installed")


class TestOptunaHyperparameterTuning:
    """Optuna hyperparameter tuning tests."""

    def test_tune_random_forest(self, trainer, sample_data):
        """Optuna tunes RandomForest and returns best params."""
        X, y = sample_data

        result = trainer.tune_hyperparameters(
            X, y,
            model_type="random_forest",
            n_trials=5,
            n_splits=3,
            timeout=60,
        )

        assert "best_params" in result
        assert "best_accuracy" in result
        assert "best_trial" in result
        assert "n_trials_completed" in result
        assert result["n_trials_completed"] == 5
        assert 0 <= result["best_accuracy"] <= 1.0
        assert "n_estimators" in result["best_params"]
        assert "max_depth" in result["best_params"]

    def test_tune_lightgbm(self, trainer, sample_data):
        """Optuna tunes LightGBM and returns best params."""
        X, y = sample_data

        try:
            import lightgbm  # noqa: F401
        except ImportError:
            pytest.skip("lightgbm not installed")

        result = trainer.tune_hyperparameters(
            X, y,
            model_type="lightgbm",
            n_trials=5,
            n_splits=3,
            timeout=60,
        )

        assert result["n_trials_completed"] == 5
        assert "learning_rate" in result["best_params"]
        assert "num_leaves" in result["best_params"]

    def test_tune_respects_timeout(self, trainer, sample_data):
        """Tuning respects timeout parameter."""
        X, y = sample_data

        result = trainer.tune_hyperparameters(
            X, y,
            model_type="random_forest",
            n_trials=1000,  # Very high, but timeout should stop it
            timeout=5,
        )

        # Should complete due to timeout, not all 1000 trials
        assert result["n_trials_completed"] < 1000

    def test_tune_small_dataset(self, trainer):
        """Tuning works with small dataset (adjusts n_splits)."""
        np.random.seed(42)
        X = pd.DataFrame({
            col: np.random.randn(20)
            for col in trainer.feature_columns
        })
        y = pd.Series(np.random.choice(["up", "down"], 20))

        result = trainer.tune_hyperparameters(
            X, y,
            model_type="random_forest",
            n_trials=3,
            timeout=30,
        )

        assert result["n_trials_completed"] == 3
