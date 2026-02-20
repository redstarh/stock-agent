"""Tests for model_registry module."""

import json
from datetime import date

import pytest
from sklearn.ensemble import RandomForestClassifier
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.ml_model import MLModel
from app.processing.model_registry import ModelRegistry


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def registry(tmp_path):
    return ModelRegistry(model_dir=str(tmp_path / "models"))


@pytest.fixture
def sample_model():
    import numpy as np
    np.random.seed(42)
    X = np.random.rand(50, 3)
    y = np.random.choice(["up", "down", "neutral"], 50)
    model = RandomForestClassifier(n_estimators=5, random_state=42)
    model.fit(X, y)
    return model


@pytest.fixture
def sample_metadata():
    return {
        "model_name": "rf_test",
        "model_version": "v1",
        "model_type": "random_forest",
        "market": "KR",
        "feature_tier": 1,
        "feature_list": ["f1", "f2", "f3"],
        "train_accuracy": 0.85,
        "test_accuracy": 0.62,
        "cv_accuracy": 0.60,
        "cv_std": 0.03,
        "train_samples": 160,
        "test_samples": 40,
        "train_start_date": date(2026, 1, 1),
        "train_end_date": date(2026, 2, 15),
        "hyperparameters": {"n_estimators": 5},
        "feature_importances": {"f1": 0.5, "f2": 0.3, "f3": 0.2},
    }


class TestSaveModel:
    def test_save_creates_record(self, registry, sample_model, sample_metadata, db):
        model_id = registry.save(sample_model, sample_metadata, db)
        assert model_id > 0

        record = db.query(MLModel).filter(MLModel.id == model_id).first()
        assert record is not None
        assert record.model_name == "rf_test"
        assert record.model_version == "v1"
        assert record.market == "KR"
        assert record.is_active is False
        assert record.model_checksum is not None
        assert len(record.model_checksum) == 64

    def test_save_creates_file(self, registry, sample_model, sample_metadata, db):
        registry.save(sample_model, sample_metadata, db)

        record = db.query(MLModel).first()
        from pathlib import Path
        assert Path(record.model_path).exists()


class TestLoadModel:
    def test_load_by_id(self, registry, sample_model, sample_metadata, db):
        import numpy as np
        model_id = registry.save(sample_model, sample_metadata, db)
        loaded = registry.load(model_id, db)

        X_test = np.random.rand(5, 3)
        assert list(loaded.predict(X_test)) == list(sample_model.predict(X_test))

    def test_load_nonexistent_raises(self, registry, db):
        with pytest.raises(ValueError, match="not found"):
            registry.load(999, db)


class TestActivateModel:
    def test_activate_deactivates_others(self, registry, sample_model, sample_metadata, db):
        # Save two models
        id1 = registry.save(sample_model, {**sample_metadata, "model_version": "v1"}, db)
        id2 = registry.save(sample_model, {**sample_metadata, "model_version": "v2"}, db)

        registry.activate(id1, db)
        assert db.query(MLModel).filter(MLModel.id == id1).first().is_active is True

        registry.activate(id2, db)
        assert db.query(MLModel).filter(MLModel.id == id1).first().is_active is False
        assert db.query(MLModel).filter(MLModel.id == id2).first().is_active is True

    def test_activate_nonexistent_raises(self, registry, db):
        with pytest.raises(ValueError, match="not found"):
            registry.activate(999, db)


class TestGetActive:
    def test_no_active(self, registry, db):
        result = registry.get_active("KR", db)
        assert result is None

    def test_get_active_after_activate(self, registry, sample_model, sample_metadata, db):
        model_id = registry.save(sample_model, sample_metadata, db)
        registry.activate(model_id, db)

        active = registry.get_active("KR", db)
        assert active is not None
        assert active.id == model_id


class TestListModels:
    def test_list_all(self, registry, sample_model, sample_metadata, db):
        registry.save(sample_model, {**sample_metadata, "model_version": "v1"}, db)
        registry.save(sample_model, {**sample_metadata, "model_version": "v2"}, db)

        models = registry.list_models(None, db)
        assert len(models) == 2

    def test_list_by_market(self, registry, sample_model, sample_metadata, db):
        registry.save(sample_model, {**sample_metadata, "market": "KR", "model_version": "v1"}, db)
        registry.save(sample_model, {**sample_metadata, "market": "US", "model_version": "v2"}, db)

        kr_models = registry.list_models("KR", db)
        assert len(kr_models) == 1
        assert kr_models[0].market == "KR"
