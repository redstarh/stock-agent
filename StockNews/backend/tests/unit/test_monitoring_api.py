"""Tests for monitoring and feature info API endpoints."""

import json
import pytest
from datetime import date, datetime, timezone, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.models.training import StockTrainingData
from app.models.ml_model import MLModel


@pytest.fixture
def client(db_session):
    """TestClient with overridden DB."""
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _seed_training(db_session, n=50, market="KR"):
    """Insert training records with labels."""
    base_date = date.today() - timedelta(days=15)
    for i in range(n):
        pred_date = base_date + timedelta(days=i % 10)
        stock_code = f"{8000 + i:06d}"
        record = StockTrainingData(
            prediction_date=pred_date,
            stock_code=stock_code,
            stock_name=f"Test {stock_code}",
            market=market,
            news_score=55.0,
            sentiment_score=0.3,
            news_count=5,
            news_count_3d=3,
            avg_score_3d=52.0,
            disclosure_ratio=0.1,
            sentiment_trend=0.05,
            prev_close=50000.0,
            prev_change_pct=1.0,
            prev_volume=100000,
            price_change_5d=2.0,
            volume_change_5d=5.0,
            ma5_ratio=1.01,
            ma20_ratio=0.99,
            volatility_5d=2.0,
            rsi_14=55.0,
            bb_position=0.5,
            market_index_change=0.3,
            market_return=0.5,
            vix_change=-0.2,
            day_of_week=pred_date.weekday(),
            predicted_direction="up",
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


class TestMonitorEndpoint:
    """GET /api/v1/training/monitor tests."""

    def test_monitor_no_active_model(self, client, db_session):
        """Monitor with no active model."""
        resp = client.get("/api/v1/training/monitor", params={"market": "KR"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["rollback_check"]["action"] == "no_active"
        assert data["alert_count"] == 0

    def test_monitor_with_healthy_model(self, client, db_session):
        """Monitor with healthy model returns ok."""
        _seed_training(db_session)
        model = MLModel(
            model_name="test_model",
            model_version="1.0",
            model_type="lightgbm",
            market="KR",
            feature_tier=1,
            feature_list=json.dumps(["rsi_14"]),
            cv_accuracy=0.62,
            train_accuracy=0.65,
            train_samples=200,
            is_active=True,
            model_path="/tmp/fake.pkl",
            model_checksum="abc",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(model)
        db_session.commit()

        resp = client.get("/api/v1/training/monitor", params={"market": "KR"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["rollback_check"]["action"] == "ok"
        assert "null_rate_report" in data
        assert "accuracy_history" in data

    def test_monitor_triggers_alert(self, client, db_session):
        """Monitor with low-accuracy model triggers alert."""
        model = MLModel(
            model_name="bad_model",
            model_version="1.0",
            model_type="lightgbm",
            market="KR",
            feature_tier=1,
            feature_list=json.dumps(["rsi_14"]),
            cv_accuracy=0.40,
            train_accuracy=0.45,
            train_samples=200,
            is_active=True,
            model_path="/tmp/fake.pkl",
            model_checksum="abc",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(model)
        db_session.commit()

        resp = client.get("/api/v1/training/monitor", params={"market": "KR"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["alert_count"] > 0


class TestFeaturesEndpoint:
    """GET /api/v1/training/features tests."""

    def test_features_returns_tiers(self, client, db_session):
        """Features endpoint returns all 3 tiers."""
        resp = client.get("/api/v1/training/features")
        assert resp.status_code == 200
        data = resp.json()
        assert "tiers" in data
        assert "1" in data["tiers"]
        assert "2" in data["tiers"]
        assert "3" in data["tiers"]

    def test_features_tier_structure(self, client, db_session):
        """Each tier has expected fields."""
        resp = client.get("/api/v1/training/features")
        data = resp.json()

        tier1 = data["tiers"]["1"]
        assert "features" in tier1
        assert "feature_count" in tier1
        assert "min_samples" in tier1
        assert "status" in tier1
        assert tier1["feature_count"] == 8
        assert tier1["min_samples"] == 200

    def test_features_includes_removed(self, client, db_session):
        """Removed features are listed with rationale."""
        resp = client.get("/api/v1/training/features")
        data = resp.json()

        assert "removed_features" in data
        assert "prev_close" in data["removed_features"]
        assert len(data["removed_features"]) > 0

    def test_features_includes_sample_counts(self, client, db_session):
        """Current sample counts are included."""
        _seed_training(db_session, n=30, market="KR")

        resp = client.get("/api/v1/training/features")
        data = resp.json()

        assert "current_samples" in data
        assert data["current_samples"]["KR"] == 30
        assert data["current_samples"]["US"] == 0
