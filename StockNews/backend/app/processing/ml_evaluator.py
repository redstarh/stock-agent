"""ML Model Evaluator — 모델 비교, 피처 중요도, A/B 테스트.

여러 모델의 성능을 비교하고 최적 모델을 선정.
"""

import logging

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import TimeSeriesSplit, cross_val_score

logger = logging.getLogger(__name__)


class MLEvaluator:
    """ML 모델 평가기."""

    def evaluate(self, model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """단일 모델 평가.

        Returns:
            {
                "accuracy": float,
                "precision": float (macro),
                "recall": float (macro),
                "f1": float (macro),
                "confusion_matrix": list[list[int]],
                "classification_report": str,
            }
        """
        preds = model.predict(X_test)

        cm = confusion_matrix(y_test, preds)

        return {
            "accuracy": round(float(accuracy_score(y_test, preds)), 4),
            "precision": round(float(precision_score(y_test, preds, average="macro", zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, preds, average="macro", zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, preds, average="macro", zero_division=0)), 4),
            "confusion_matrix": cm.tolist(),
            "classification_report": classification_report(y_test, preds, zero_division=0),
        }

    def compare_models(
        self, models: dict, X_test: pd.DataFrame, y_test: pd.Series
    ) -> pd.DataFrame:
        """여러 모델 비교. Best model 선정.

        Args:
            models: {"model_name": model_object, ...}

        Returns:
            DataFrame with columns: model_name, accuracy, precision, recall, f1
            Sorted by accuracy descending.
        """
        results = []
        for name, model in models.items():
            metrics = self.evaluate(model, X_test, y_test)
            results.append({
                "model_name": name,
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
            })

        df = pd.DataFrame(results)
        df = df.sort_values("accuracy", ascending=False).reset_index(drop=True)
        return df

    def feature_importance(
        self, model, feature_names: list[str]
    ) -> list[dict]:
        """피처 중요도 분석. Returns sorted list.

        Returns:
            [{"name": str, "importance": float}, ...] sorted desc.
        """
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        else:
            logger.warning("Model does not have feature_importances_ attribute")
            return []

        result = [
            {"name": name, "importance": round(float(imp), 4)}
            for name, imp in zip(feature_names, importances)
        ]

        return sorted(result, key=lambda x: x["importance"], reverse=True)

    def ab_test_features(
        self, model_class, X_a: pd.DataFrame, y_a: pd.Series,
        X_b: pd.DataFrame, y_b: pd.Series,
        n_splits: int = 5,
    ) -> dict:
        """Tier A vs Tier B 정확도 비교.

        Uses same model class with different feature sets.

        Returns:
            {
                "tier_a_accuracy": float, "tier_a_std": float,
                "tier_b_accuracy": float, "tier_b_std": float,
                "improvement": float (B - A),
                "is_significant": bool (improvement > 2%)
            }
        """
        n_splits_a = min(n_splits, len(X_a) // 2)
        n_splits_b = min(n_splits, len(X_b) // 2)
        if n_splits_a < 2:
            n_splits_a = 2
        if n_splits_b < 2:
            n_splits_b = 2

        tscv_a = TimeSeriesSplit(n_splits=n_splits_a)
        tscv_b = TimeSeriesSplit(n_splits=n_splits_b)

        model_a = model_class()
        model_b = model_class()

        scores_a = cross_val_score(model_a, X_a, y_a, cv=tscv_a, scoring="accuracy")
        scores_b = cross_val_score(model_b, X_b, y_b, cv=tscv_b, scoring="accuracy")

        mean_a = float(np.mean(scores_a))
        mean_b = float(np.mean(scores_b))
        improvement = mean_b - mean_a

        return {
            "tier_a_accuracy": round(mean_a, 4),
            "tier_a_std": round(float(np.std(scores_a)), 4),
            "tier_b_accuracy": round(mean_b, 4),
            "tier_b_std": round(float(np.std(scores_b)), 4),
            "improvement": round(improvement, 4),
            "is_significant": improvement > 0.02,
        }
