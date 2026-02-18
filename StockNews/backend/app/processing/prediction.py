"""뉴스 기반 주가 방향 예측 모델."""

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import numpy as np


class NewsPredictionModel:
    """뉴스 피처 기반 주가 방향 예측 모델."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight="balanced",
        )
        self._is_trained = False

    def train(self, features: list[list[float]], labels: list[str]) -> dict:
        """모델 학습. Returns training metrics dict."""
        X = np.array(features)
        y = np.array(labels)

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self._is_trained = True

        # Cross-validation score
        cv_scores = cross_val_score(
            self.model, X_scaled, y, cv=min(5, len(X)), scoring="accuracy"
        )

        return {
            "accuracy": float(cv_scores.mean()),
            "std": float(cv_scores.std()),
            "n_samples": len(X),
        }

    def predict(self, features: list[list[float]]) -> list[dict]:
        """예측 수행. Returns list of {direction, confidence}."""
        if not self._is_trained:
            raise RuntimeError("Model not trained")

        X = np.array(features)
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)

        results = []
        for pred, proba in zip(predictions, probabilities):
            confidence = float(max(proba))
            results.append({"direction": str(pred), "confidence": confidence})

        return results

    def predict_single(
        self,
        news_score: float,
        sentiment_score: float,
        news_count: int,
        avg_score_3d: float,
    ) -> dict:
        """단일 종목 예측."""
        features = [[news_score, sentiment_score, float(news_count), avg_score_3d]]
        return self.predict(features)[0]

    @property
    def is_trained(self) -> bool:
        return self._is_trained


def run_backtest(
    model: NewsPredictionModel,
    features: list[list[float]],
    labels: list[str],
    train_ratio: float = 0.7,
) -> dict:
    """시간순 분할 백테스트.

    Returns: {accuracy, correlation, n_train, n_test, predictions}
    """
    n = len(features)
    split_idx = int(n * train_ratio)

    train_X, test_X = features[:split_idx], features[split_idx:]
    train_y, test_y = labels[:split_idx], labels[split_idx:]

    model.train(train_X, train_y)
    predictions = model.predict(test_X)

    pred_directions = [p["direction"] for p in predictions]

    # Accuracy
    correct = sum(1 for p, a in zip(pred_directions, test_y) if p == a)
    accuracy = correct / len(test_y) if test_y else 0.0

    # Correlation (direction → numeric: up=1, neutral=0, down=-1)
    dir_to_num = {"up": 1, "down": -1, "neutral": 0}
    pred_nums = [dir_to_num.get(d, 0) for d in pred_directions]
    actual_nums = [dir_to_num.get(d, 0) for d in test_y]

    # Pearson correlation
    if len(set(pred_nums)) > 1 and len(set(actual_nums)) > 1:
        correlation = float(np.corrcoef(pred_nums, actual_nums)[0, 1])
    else:
        correlation = 0.0

    return {
        "accuracy": accuracy,
        "correlation": correlation,
        "n_train": len(train_X),
        "n_test": len(test_X),
        "predictions": predictions,
    }
