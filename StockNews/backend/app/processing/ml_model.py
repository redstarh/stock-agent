"""Enhanced ML model with price + news features."""

import logging
import os
from pathlib import Path
from typing import Optional

from collections import Counter

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.collectors.price_collector import PriceCollector
from app.processing.feature_engineer import build_feature_vector, prepare_training_data


class EnhancedPredictionModel:
    """뉴스 + 주가 피처 기반 예측 모델."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight="balanced",
        )
        self._is_trained = False

    def train(self, features: list[list[float]], labels: list[str]) -> dict:
        """모델 학습.

        Args:
            features: Feature vectors (8-dimensional)
            labels: Target labels ("up", "down", "neutral")

        Returns:
            Training metrics dict
        """
        if len(features) < 5:
            raise ValueError("Need at least 5 samples for training")

        X = np.array(features)
        y = np.array(labels)

        logger.info(f"Training model with {len(X)} samples")

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self._is_trained = True

        # Cross-validation (StratifiedKFold requires each class to have >= n_splits members)
        class_counts = Counter(y)
        min_class_count = min(class_counts.values())
        cv_folds = min(5, min_class_count)
        if cv_folds >= 2:
            cv_scores = cross_val_score(
                self.model, X_scaled, y, cv=cv_folds, scoring="accuracy"
            )
        else:
            # Too few samples per class for CV — report training accuracy
            cv_scores = np.array([self.model.score(X_scaled, y)])

        metrics = {
            "accuracy": float(cv_scores.mean()),
            "std": float(cv_scores.std()),
            "n_samples": len(X),
            "cv_folds": cv_folds,
        }

        logger.info(f"Training completed: accuracy={metrics['accuracy']:.3f}")
        return metrics

    def predict(self, features: list[list[float]]) -> list[dict]:
        """예측 수행.

        Args:
            features: Feature vectors

        Returns:
            List of {"direction": str, "confidence": float}
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained")

        X = np.array(features)
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)

        results = []
        for pred, proba in zip(predictions, probabilities):
            confidence = float(max(proba))
            results.append({"direction": str(pred), "confidence": round(confidence, 3)})

        return results

    def predict_direction(
        self,
        stock_code: str,
        db: Session,
        collector: Optional[PriceCollector] = None,
    ) -> dict:
        """종목의 주가 방향 예측.

        Args:
            stock_code: 종목 코드
            db: Database session
            collector: PriceCollector 인스턴스

        Returns:
            {"direction": "up"|"down"|"neutral", "confidence": float}
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained")

        features = build_feature_vector(stock_code, db, collector)

        feature_vec = [
            features["news_score"],
            features["sentiment_score"],
            float(features["news_count"]),
            features["avg_score_3d"],
            features["disclosure_ratio"],
            features["price_change_pct"],
            features["volume_change_pct"],
            features["moving_average_ratio"],
        ]

        result = self.predict([feature_vec])[0]
        logger.info(f"Prediction for {stock_code}: {result}")
        return result

    def backtest(
        self,
        stock_code: str,
        db: Session,
        test_days: int = 30,
        collector: Optional[PriceCollector] = None,
    ) -> dict:
        """단일 종목 백테스트 (간단한 버전).

        Args:
            stock_code: 종목 코드
            db: Database session
            test_days: 테스트 기간 (일)
            collector: PriceCollector 인스턴스

        Returns:
            {"accuracy": float, "predictions": list}
        """
        logger.info(f"Backtesting {stock_code} for {test_days} days")

        # 실제 백테스트는 시계열 분할이 필요하므로
        # 여기서는 간단히 현재 예측만 수행
        try:
            prediction = self.predict_direction(stock_code, db, collector)
            features = build_feature_vector(stock_code, db, collector)

            # 실제 방향 계산
            price_change = features["price_change_pct"]
            if price_change > 2.0:
                actual = "up"
            elif price_change < -2.0:
                actual = "down"
            else:
                actual = "neutral"

            accuracy = 1.0 if prediction["direction"] == actual else 0.0

            return {
                "accuracy": accuracy,
                "predictions": [
                    {
                        "predicted": prediction["direction"],
                        "actual": actual,
                        "confidence": prediction["confidence"],
                    }
                ],
            }

        except Exception as e:
            logger.error(f"Backtest failed for {stock_code}: {e}")
            return {"accuracy": 0.0, "predictions": []}

    def save_model(self, filepath: str):
        """모델 저장.

        Args:
            filepath: 저장 경로
        """
        if not self._is_trained:
            raise RuntimeError("Cannot save untrained model")

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "is_trained": self._is_trained,
        }

        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """모델 로드.

        Args:
            filepath: 모델 파일 경로
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        model_data = joblib.load(filepath)
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self._is_trained = model_data["is_trained"]

        logger.info(f"Model loaded from {filepath}")

    @property
    def is_trained(self) -> bool:
        return self._is_trained


def train_model_from_db(
    stock_codes: list[str],
    db: Session,
    collector: Optional[PriceCollector] = None,
) -> tuple[EnhancedPredictionModel, dict]:
    """DB에서 데이터를 가져와 모델 학습.

    Args:
        stock_codes: 학습할 종목 코드 리스트
        db: Database session
        collector: PriceCollector 인스턴스

    Returns:
        (trained_model, metrics)
    """
    logger.info(f"Training model with {len(stock_codes)} stocks")

    features, labels, valid_codes = prepare_training_data(stock_codes, db, collector)

    model = EnhancedPredictionModel()
    metrics = model.train(features, labels)

    logger.info(f"Model training completed for {len(valid_codes)} stocks")
    return model, metrics
