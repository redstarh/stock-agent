"""ML Training Pipeline — LightGBM + RandomForest with TimeSeriesSplit.

Data Leakage Prevention: TimeSeriesSplit만 사용. Random split 금지.
Train dates < validation dates < test dates 보장.
"""

import hashlib
import logging
import pickle
from datetime import date
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
        except ImportError:
            raise ImportError("lightgbm is required. Install: pip install lightgbm>=4.0.0")

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
            [float(v) for v in model.feature_importances_],
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
            [float(v) for v in model.feature_importances_],
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
