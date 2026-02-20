"""Extended training API integration tests."""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timezone, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.training import StockTrainingData
from app.models.ml_model import MLModel


@pytest.fixture
def client(db_session):
    """TestClient with overridden DB dependency."""
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _seed_training_data(db_session, n=250, market="KR"):
    """Insert n training records with labels."""
    base_date = date(2026, 1, 1)
    for i in range(n):
        pred_date = base_date + timedelta(days=i // 10)
        stock_code = f"{i % 10:06d}"
        record = StockTrainingData(
            prediction_date=pred_date,
            stock_code=stock_code,
            stock_name=f"Test {stock_code}",
            market=market,
            news_score=50.0 + (i % 30),
            sentiment_score=0.3,
            news_count=5,
            news_count_3d=3,
            avg_score_3d=52.0,
            disclosure_ratio=0.1,
            sentiment_trend=0.05,
            prev_close=50000.0,
            prev_change_pct=1.0 + (i % 5),
            prev_volume=100000,
            price_change_5d=2.0,
            volume_change_5d=5.0,
            ma5_ratio=1.01,
            ma20_ratio=0.99,
            volatility_5d=2.0,
            rsi_14=50.0 + (i % 20),
            bb_position=0.5,
            market_index_change=0.3,
            market_return=0.5,
            vix_change=-0.2,
            day_of_week=pred_date.weekday(),
            predicted_direction="up" if i % 3 != 2 else "down",
            predicted_score=65.0,
            confidence=0.7,
            actual_close=51000.0,
            actual_change_pct=2.0 if i % 2 == 0 else -1.0,
            actual_direction="up" if i % 2 == 0 else "down",
            actual_volume=110000,
            is_correct=(i % 2 == 0),
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(record)
    db_session.commit()


class TestTrainEndpoint:
    """POST /api/v1/training/train tests."""

    def test_train_insufficient_data(self, client, db_session):
        """Insufficient data returns proper status."""
        # No data seeded — should return insufficient
        resp = client.post(
            "/api/v1/training/train",
            params={"market": "KR", "model_type": "lightgbm", "feature_tier": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "insufficient_data"
        assert data["required"] == 200

    def test_train_success(self, client, db_session):
        """Successful training returns model info."""
        _seed_training_data(db_session, n=250, market="KR")

        resp = client.post(
            "/api/v1/training/train",
            params={"market": "KR", "model_type": "random_forest", "feature_tier": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "trained"
        assert "model_id" in data
        assert data["model_type"] == "random_forest"
        assert data["features"] == 8
        assert data["train_accuracy"] > 0


class TestModelsEndpoint:
    """GET /api/v1/training/models tests."""

    def test_list_models_empty(self, client, db_session):
        """Empty model list."""
        resp = client.get("/api/v1/training/models")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_models_after_train(self, client, db_session):
        """Model appears after training."""
        _seed_training_data(db_session, n=250, market="KR")

        # Train a model first
        client.post(
            "/api/v1/training/train",
            params={"market": "KR", "model_type": "random_forest", "feature_tier": 1},
        )

        resp = client.get("/api/v1/training/models", params={"market": "KR"})
        assert resp.status_code == 200
        models = resp.json()
        assert len(models) >= 1
        assert models[0]["market"] == "KR"
        assert models[0]["feature_tier"] == 1


class TestActivateEndpoint:
    """POST /api/v1/training/models/{id}/activate tests."""

    def test_activate_nonexistent(self, client, db_session):
        """Activating nonexistent model returns 404."""
        resp = client.post("/api/v1/training/models/99999/activate")
        assert resp.status_code == 404

    def test_activate_success(self, client, db_session):
        """Activate a trained model."""
        _seed_training_data(db_session, n=250, market="KR")

        train_resp = client.post(
            "/api/v1/training/train",
            params={"market": "KR", "model_type": "random_forest", "feature_tier": 1},
        )
        model_id = train_resp.json()["model_id"]

        resp = client.post(f"/api/v1/training/models/{model_id}/activate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "activated"


class TestEvaluateEndpoint:
    """POST /api/v1/training/evaluate tests."""

    def test_evaluate_no_active(self, client, db_session):
        """No active model returns proper status."""
        resp = client.post("/api/v1/training/evaluate", params={"market": "KR"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_active_model"

    def test_evaluate_success(self, client, db_session):
        """Evaluate active model."""
        _seed_training_data(db_session, n=250, market="KR")

        # Train
        train_resp = client.post(
            "/api/v1/training/train",
            params={"market": "KR", "model_type": "random_forest", "feature_tier": 1},
        )
        model_id = train_resp.json()["model_id"]

        # Activate
        client.post(f"/api/v1/training/models/{model_id}/activate")

        # Evaluate
        resp = client.post("/api/v1/training/evaluate", params={"market": "KR"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "evaluated"
        assert "accuracy" in data
