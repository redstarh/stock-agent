"""Tests for ml_evaluator module."""

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from app.processing.ml_evaluator import MLEvaluator


@pytest.fixture
def evaluator():
    return MLEvaluator()


@pytest.fixture
def trained_model():
    """Pre-trained RandomForest for testing."""
    np.random.seed(42)
    X = pd.DataFrame({
        "f1": np.random.uniform(0, 100, 200),
        "f2": np.random.uniform(-1, 1, 200),
        "f3": np.random.uniform(0, 100, 200),
    })
    y = pd.Series(np.random.choice(["up", "down", "neutral"], 200))

    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    return model, X, y


class TestEvaluate:
    def test_basic_evaluation(self, evaluator, trained_model):
        model, X, y = trained_model
        result = evaluator.evaluate(model, X, y)

        assert "accuracy" in result
        assert "precision" in result
        assert "recall" in result
        assert "f1" in result
        assert "confusion_matrix" in result
        assert "classification_report" in result
        assert 0 <= result["accuracy"] <= 1.0
        assert 0 <= result["precision"] <= 1.0

    def test_confusion_matrix_shape(self, evaluator, trained_model):
        model, X, y = trained_model
        result = evaluator.evaluate(model, X, y)
        cm = result["confusion_matrix"]
        assert len(cm) == 3  # 3 classes
        assert all(len(row) == 3 for row in cm)


class TestCompareModels:
    def test_compare_two_models(self, evaluator):
        np.random.seed(42)
        X = pd.DataFrame({
            "f1": np.random.uniform(0, 100, 200),
            "f2": np.random.uniform(-1, 1, 200),
        })
        y = pd.Series(np.random.choice(["up", "down", "neutral"], 200))

        rf1 = RandomForestClassifier(n_estimators=10, random_state=42)
        rf2 = RandomForestClassifier(n_estimators=100, random_state=42)
        rf1.fit(X, y)
        rf2.fit(X, y)

        result = evaluator.compare_models({"rf_10": rf1, "rf_100": rf2}, X, y)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "model_name" in result.columns
        assert "accuracy" in result.columns
        # Sorted by accuracy desc
        assert result.iloc[0]["accuracy"] >= result.iloc[1]["accuracy"]

    def test_single_model(self, evaluator, trained_model):
        model, X, y = trained_model
        result = evaluator.compare_models({"single": model}, X, y)
        assert len(result) == 1


class TestFeatureImportance:
    def test_sorted_descending(self, evaluator, trained_model):
        model, X, y = trained_model
        result = evaluator.feature_importance(model, ["f1", "f2", "f3"])

        assert len(result) == 3
        assert all("name" in item and "importance" in item for item in result)
        # Check sorted descending
        importances = [item["importance"] for item in result]
        assert importances == sorted(importances, reverse=True)

    def test_no_feature_importances(self, evaluator):
        """Model without feature_importances_ attribute."""

        class DummyModel:
            pass

        result = evaluator.feature_importance(DummyModel(), ["f1"])
        assert result == []


class TestABTestFeatures:
    def test_ab_test(self, evaluator):
        np.random.seed(42)
        n = 200

        X_a = pd.DataFrame({
            "f1": np.random.uniform(0, 100, n),
            "f2": np.random.uniform(-1, 1, n),
        })
        X_b = pd.DataFrame({
            "f1": np.random.uniform(0, 100, n),
            "f2": np.random.uniform(-1, 1, n),
            "f3": np.random.uniform(0, 50, n),
        })
        y = pd.Series(np.random.choice(["up", "down", "neutral"], n))

        result = evaluator.ab_test_features(
            lambda: RandomForestClassifier(n_estimators=20, random_state=42),
            X_a, y, X_b, y, n_splits=3,
        )

        assert "tier_a_accuracy" in result
        assert "tier_b_accuracy" in result
        assert "improvement" in result
        assert "is_significant" in result
        assert isinstance(result["is_significant"], bool)
