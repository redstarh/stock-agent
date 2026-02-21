"""ML Training Pipeline — LightGBM + RandomForest with TimeSeriesSplit.

Data Leakage Prevention: TimeSeriesSplit만 사용. Random split 금지.
Train dates < validation dates < test dates 보장.
"""

import hashlib
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sqlalchemy.orm import Session

from app.models.training import StockTrainingData
from app.processing.feature_config import get_features_for_tier, get_min_samples_for_tier

logger = logging.getLogger(__name__)

# Direction label mapping
DIRECTION_MAP = {"up": 0, "neutral": 1, "down": 2}
DIRECTION_LABELS = ["up", "neutral", "down"]


class MLTrainer:
    """LightGBM + RandomForest 학습 파이프라인."""

    def __init__(self, market: str, tier: int = 1):
        self.market = market
        self.tier = tier
        self.feature_columns = get_features_for_tier(tier)
        self.min_samples = get_min_samples_for_tier(tier)

    def load_training_data(self, db: Session) -> tuple[pd.DataFrame, pd.Series]:
        """DB에서 labeled data 로드. TimeSeriesSplit 준비.

        Returns:
            (X, y) — features DataFrame and direction labels Series.
            Sorted by prediction_date for TimeSeriesSplit.

        Raises:
            ValueError: If insufficient labeled samples.
        """
        records = (
            db.query(StockTrainingData)
            .filter(
                StockTrainingData.market == self.market,
                StockTrainingData.actual_direction.isnot(None),
            )
            .order_by(StockTrainingData.prediction_date)
            .all()
        )

        if len(records) < self.min_samples:
            raise ValueError(
                f"Insufficient samples: {len(records)} < {self.min_samples} "
                f"(required for Tier {self.tier})"
            )

        rows = []
        labels = []
        for r in records:
            row = {}
            for col in self.feature_columns:
                val = getattr(r, col, None)
                row[col] = float(val) if val is not None else 0.0
            rows.append(row)
            labels.append(r.actual_direction)

        X = pd.DataFrame(rows, columns=self.feature_columns)
        y = pd.Series(labels)

        return X, y

    def train_lightgbm(self, X: pd.DataFrame, y: pd.Series, **params) -> dict:
        """LightGBM 학습.

        Returns:
            {"model": model, "accuracy": float, "cv_accuracy": float,
             "cv_std": float, "feature_importances": dict}
        """
        try:
            import lightgbm as lgb
        except ImportError as err:
            raise ImportError("lightgbm is required. Install: pip install lightgbm>=4.0.0") from err

        default_params = {
            "n_estimators": 100,
            "max_depth": 5,
            "learning_rate": 0.1,
            "num_leaves": 31,
            "random_state": 42,
            "verbose": -1,
            "n_jobs": -1,
        }
        default_params.update(params)

        model = lgb.LGBMClassifier(**default_params)

        # Cross-validation with TimeSeriesSplit
        cv_result = self.cross_validate(model, X, y)

        # Final fit on all data
        model.fit(X, y)

        # Feature importances
        importances = dict(zip(
            self.feature_columns,
            [float(v) for v in model.feature_importances_], strict=False,
        ))

        return {
            "model": model,
            "accuracy": float(model.score(X, y)),
            "cv_accuracy": cv_result["cv_accuracy"],
            "cv_std": cv_result["cv_std"],
            "feature_importances": importances,
        }

    def train_random_forest(self, X: pd.DataFrame, y: pd.Series, **params) -> dict:
        """RandomForest 학습.

        Returns:
            Same format as train_lightgbm.
        """
        default_params = {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42,
            "n_jobs": -1,
        }
        default_params.update(params)

        model = RandomForestClassifier(**default_params)

        # Cross-validation
        cv_result = self.cross_validate(model, X, y)

        # Final fit
        model.fit(X, y)

        importances = dict(zip(
            self.feature_columns,
            [float(v) for v in model.feature_importances_], strict=False,
        ))

        return {
            "model": model,
            "accuracy": float(model.score(X, y)),
            "cv_accuracy": cv_result["cv_accuracy"],
            "cv_std": cv_result["cv_std"],
            "feature_importances": importances,
        }

    def cross_validate(
        self, model, X: pd.DataFrame, y: pd.Series, n_splits: int = 5
    ) -> dict:
        """TimeSeriesSplit CV. Never random split.

        Returns:
            {"cv_accuracy": float, "cv_std": float, "cv_scores": list[float]}
        """
        n_splits = min(n_splits, len(X) // 2)
        if n_splits < 2:
            n_splits = 2

        tscv = TimeSeriesSplit(n_splits=n_splits)
        scores = cross_val_score(model, X, y, cv=tscv, scoring="accuracy")

        return {
            "cv_accuracy": round(float(np.mean(scores)), 4),
            "cv_std": round(float(np.std(scores)), 4),
            "cv_scores": [round(float(s), 4) for s in scores],
        }

    def save_model(self, model, name: str, version: str, output_dir: str = "models") -> dict:
        """Pickle + SHA-256 checksum 저장.

        Returns:
            {"path": str, "checksum": str, "size_bytes": int}
        """
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)

        filename = f"{name}_{self.market}_t{self.tier}_{version}.pkl"
        filepath = path / filename

        data = pickle.dumps(model)
        checksum = hashlib.sha256(data).hexdigest()

        filepath.write_bytes(data)

        return {
            "path": str(filepath),
            "checksum": checksum,
            "size_bytes": len(data),
        }

    @staticmethod
    def load_model(filepath: str, expected_checksum: str | None = None):
        """Pickle 로드 + checksum 검증.

        Raises:
            ValueError: If checksum mismatch.
        """
        data = Path(filepath).read_bytes()

        if expected_checksum:
            actual = hashlib.sha256(data).hexdigest()
            if actual != expected_checksum:
                raise ValueError(
                    f"Model checksum mismatch: expected {expected_checksum}, got {actual}"
                )

        return pickle.loads(data)

    def shap_feature_importance(self, model, X: pd.DataFrame) -> dict:
        """SHAP 기반 피처 중요도 분석.

        TreeExplainer for LightGBM/RandomForest.
        Returns sorted feature importance with SHAP values.

        Returns:
            {
                "feature_importances": [{"name": str, "importance": float}, ...],
                "mean_shap_values": dict[str, float],
            }
        """
        try:
            import shap
        except ImportError as err:
            raise ImportError("shap is required. Install: pip install shap>=0.43.0") from err

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        # For multi-class, shap_values can be:
        # - list of arrays (one per class): [(n_samples, n_features), ...]
        # - single 3D array: (n_samples, n_features, n_classes)
        if isinstance(shap_values, list):
            # List format: stack and take mean absolute across classes
            shap_array = np.stack([np.abs(sv) for sv in shap_values], axis=-1)
            mean_abs_per_class = np.mean(shap_array, axis=-1)  # Average across classes
        else:
            # 3D array format
            if shap_values.ndim == 3:
                # (n_samples, n_features, n_classes) -> mean abs across classes
                mean_abs_per_class = np.mean(np.abs(shap_values), axis=-1)
            else:
                # Binary classification: (n_samples, n_features)
                mean_abs_per_class = np.abs(shap_values)

        # Mean across samples to get feature importance
        feature_importance = np.mean(mean_abs_per_class, axis=0)

        # Normalize to sum to 1
        total = feature_importance.sum()
        if total > 0:
            feature_importance = feature_importance / total

        result = [
            {"name": name, "importance": round(float(imp), 4)}
            for name, imp in zip(self.feature_columns, feature_importance, strict=False)
        ]
        result.sort(key=lambda x: x["importance"], reverse=True)

        mean_shap = {
            name: round(float(imp), 4)
            for name, imp in zip(self.feature_columns, feature_importance, strict=False)
        }

        return {
            "feature_importances": result,
            "mean_shap_values": mean_shap,
        }

    def tune_hyperparameters(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: str = "lightgbm",
        n_trials: int = 30,
        n_splits: int = 5,
        timeout: int = 300,
    ) -> dict:
        """Optuna 기반 하이퍼파라미터 최적화.

        TimeSeriesSplit CV로 평가. Random split 사용 금지.

        Args:
            model_type: "lightgbm" or "random_forest"
            n_trials: Number of Optuna trials
            n_splits: TimeSeriesSplit folds
            timeout: Max seconds for optimization

        Returns:
            {
                "best_params": dict,
                "best_accuracy": float,
                "best_trial": int,
                "n_trials_completed": int,
            }
        """
        try:
            import optuna
        except ImportError as err:
            raise ImportError("optuna is required. Install: pip install optuna>=3.5.0") from err

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        n_splits = min(n_splits, len(X) // 2)
        if n_splits < 2:
            n_splits = 2

        tscv = TimeSeriesSplit(n_splits=n_splits)

        def objective(trial):
            if model_type == "lightgbm":
                try:
                    import lightgbm as lgb
                except ImportError as err:
                    raise ImportError("lightgbm required for tuning") from err

                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "max_depth": trial.suggest_int("max_depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    "num_leaves": trial.suggest_int("num_leaves", 15, 63),
                    "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "random_state": 42,
                    "verbose": -1,
                    "n_jobs": -1,
                }
                model = lgb.LGBMClassifier(**params)
            else:
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "max_depth": trial.suggest_int("max_depth", 3, 15),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                    "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                    "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
                    "random_state": 42,
                    "n_jobs": -1,
                }
                model = RandomForestClassifier(**params)

            scores = cross_val_score(model, X, y, cv=tscv, scoring="accuracy")
            return float(np.mean(scores))

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, timeout=timeout)

        return {
            "best_params": study.best_params,
            "best_accuracy": round(study.best_value, 4),
            "best_trial": study.best_trial.number,
            "n_trials_completed": len(study.trials),
        }
