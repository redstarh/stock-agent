"""Tests for model auto-rollback and accuracy monitoring."""

import json
import pytest
from datetime import datetime, timezone

from app.models.ml_model import MLModel
from app.processing.model_registry import ModelRegistry


@pytest.fixture
def registry(tmp_path):
    """ModelRegistry with temp directory."""
    return ModelRegistry(model_dir=str(tmp_path / "models"))


def _create_ml_model(db_session, **overrides):
    """Helper to create MLModel records."""
    defaults = {
        "model_name": "test_model",
        "model_version": "1.0",
        "model_type": "lightgbm",
        "market": "KR",
        "feature_tier": 1,
        "feature_list": json.dumps(["rsi_14", "news_score"]),
        "cv_accuracy": 0.60,
        "train_accuracy": 0.65,
        "train_samples": 200,
        "is_active": False,
        "model_path": "/tmp/fake.pkl",
        "model_checksum": "abc123",
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    record = MLModel(**defaults)
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


class TestCheckAccuracyAndRollback:
    """Auto-rollback tests."""

    def test_no_active_model(self, registry, db_session):
        """No active model returns no_active."""
        result = registry.check_accuracy_and_rollback("KR", db_session)
        assert result["action"] == "no_active"

    def test_accuracy_ok(self, registry, db_session):
        """Active model above threshold returns ok."""
        _create_ml_model(db_session, is_active=True, cv_accuracy=0.62)

        result = registry.check_accuracy_and_rollback("KR", db_session, min_accuracy=0.55)
        assert result["action"] == "ok"
        assert result["active_accuracy"] == 0.62

    def test_rollback_triggered(self, registry, db_session):
        """Low accuracy triggers rollback to best alternative."""
        # Create low-accuracy active model
        active = _create_ml_model(
            db_session, model_name="bad_model", is_active=True, cv_accuracy=0.45
        )

        # Create good alternative
        good = _create_ml_model(
            db_session, model_name="good_model", is_active=False, cv_accuracy=0.62
        )

        result = registry.check_accuracy_and_rollback("KR", db_session, min_accuracy=0.55)

        assert result["action"] == "rollback"
        assert result["active_model_id"] == active.id
        assert result["rollback_to_id"] == good.id
        assert result["rollback_accuracy"] == 0.62

        # Verify the good model is now active
        db_session.refresh(good)
        assert good.is_active is True

    def test_no_fallback_available(self, registry, db_session):
        """No better alternative returns no_fallback."""
        _create_ml_model(
            db_session, model_name="bad_active", is_active=True, cv_accuracy=0.45
        )
        _create_ml_model(
            db_session, model_name="also_bad", is_active=False, cv_accuracy=0.40
        )

        result = registry.check_accuracy_and_rollback("KR", db_session, min_accuracy=0.55)
        assert result["action"] == "no_fallback"

    def test_rollback_selects_best(self, registry, db_session):
        """Rollback picks the highest accuracy alternative."""
        _create_ml_model(
            db_session, model_name="active_bad", is_active=True, cv_accuracy=0.45
        )
        _create_ml_model(
            db_session, model_name="alt_ok", is_active=False, cv_accuracy=0.58
        )
        best = _create_ml_model(
            db_session, model_name="alt_best", is_active=False, cv_accuracy=0.65
        )

        result = registry.check_accuracy_and_rollback("KR", db_session, min_accuracy=0.55)
        assert result["rollback_to_id"] == best.id

    def test_market_isolation(self, registry, db_session):
        """Rollback only considers models from same market."""
        _create_ml_model(
            db_session, model_name="kr_bad", market="KR", is_active=True, cv_accuracy=0.45
        )
        # Good model but for US market
        _create_ml_model(
            db_session, model_name="us_good", market="US", is_active=False, cv_accuracy=0.70
        )

        result = registry.check_accuracy_and_rollback("KR", db_session, min_accuracy=0.55)
        assert result["action"] == "no_fallback"


class TestAccuracyHistory:
    """Accuracy history tests."""

    def test_empty_history(self, registry, db_session):
        """Empty history for market with no models."""
        result = registry.get_accuracy_history("KR", db_session)
        assert result == []

    def test_history_returns_models(self, registry, db_session):
        """Returns models ordered by created_at desc."""
        _create_ml_model(db_session, model_name="model_1", cv_accuracy=0.55)
        _create_ml_model(db_session, model_name="model_2", cv_accuracy=0.60, is_active=True)

        result = registry.get_accuracy_history("KR", db_session)
        assert len(result) == 2
        # Most recent first
        assert result[0]["model_name"] == "model_2"
        assert result[0]["is_active"] is True

    def test_history_respects_limit(self, registry, db_session):
        """History respects limit parameter."""
        for i in range(5):
            _create_ml_model(db_session, model_name=f"model_{i}", cv_accuracy=0.50 + i * 0.02)

        result = registry.get_accuracy_history("KR", db_session, limit=3)
        assert len(result) == 3
