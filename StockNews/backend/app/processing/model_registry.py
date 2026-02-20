"""ML Model Registry — 모델 저장, 로드, 버전 관리.

모델 파일을 pickle로 저장하고, DB에 메타데이터를 기록.
활성 모델 관리, checksum 검증 포함.
"""

import hashlib
import json
import logging
import pickle
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.ml_model import MLModel

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = "models"


class ModelRegistry:
    """ML 모델 레지스트리."""

    def __init__(self, model_dir: str = DEFAULT_MODEL_DIR):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        model,
        metadata: dict,
        db: Session,
    ) -> int:
        """모델 파일 저장 + DB 레코드 생성.

        Args:
            model: Trained model object (sklearn/lightgbm)
            metadata: {
                "model_name": str,
                "model_version": str,
                "model_type": str ("lightgbm" | "random_forest"),
                "market": str,
                "feature_tier": int,
                "feature_list": list[str],
                "train_accuracy": float,
                "test_accuracy": float | None,
                "cv_accuracy": float,
                "cv_std": float,
                "train_samples": int,
                "test_samples": int | None,
                "train_start_date": date | None,
                "train_end_date": date | None,
                "hyperparameters": dict | None,
                "feature_importances": dict | None,
            }
            db: Database session

        Returns:
            Model ID (int)
        """
        # Serialize model
        model_data = pickle.dumps(model)
        checksum = hashlib.sha256(model_data).hexdigest()

        # Save file
        filename = f"{metadata['model_name']}_{metadata['market']}_t{metadata['feature_tier']}_{metadata['model_version']}.pkl"
        filepath = self.model_dir / filename
        filepath.write_bytes(model_data)

        # Create DB record
        record = MLModel(
            model_name=metadata["model_name"],
            model_version=metadata["model_version"],
            model_type=metadata["model_type"],
            market=metadata["market"],
            feature_tier=metadata["feature_tier"],
            feature_list=json.dumps(metadata["feature_list"]),
            train_accuracy=metadata.get("train_accuracy"),
            test_accuracy=metadata.get("test_accuracy"),
            cv_accuracy=metadata.get("cv_accuracy"),
            cv_std=metadata.get("cv_std"),
            train_samples=metadata.get("train_samples"),
            test_samples=metadata.get("test_samples"),
            train_start_date=metadata.get("train_start_date"),
            train_end_date=metadata.get("train_end_date"),
            is_active=False,
            model_path=str(filepath),
            model_checksum=checksum,
            hyperparameters=json.dumps(metadata.get("hyperparameters")) if metadata.get("hyperparameters") else None,
            feature_importances=json.dumps(metadata.get("feature_importances")) if metadata.get("feature_importances") else None,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info("Saved model %s v%s (id=%d) to %s", metadata["model_name"], metadata["model_version"], record.id, filepath)
        return record.id

    def load(self, model_id: int, db: Session):
        """모델 로드 (ID 기반). Checksum 검증.

        Raises:
            ValueError: If model not found or checksum mismatch.
        """
        record = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not record:
            raise ValueError(f"Model ID {model_id} not found")

        filepath = Path(record.model_path)
        if not filepath.exists():
            raise ValueError(f"Model file not found: {filepath}")

        data = filepath.read_bytes()

        if record.model_checksum:
            actual = hashlib.sha256(data).hexdigest()
            if actual != record.model_checksum:
                raise ValueError(f"Checksum mismatch for model {model_id}")

        return pickle.loads(data)

    def activate(self, model_id: int, db: Session) -> None:
        """모델 활성화 (같은 시장의 다른 모델은 비활성화).

        Raises:
            ValueError: If model not found.
        """
        record = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not record:
            raise ValueError(f"Model ID {model_id} not found")

        # Deactivate all models for this market
        db.query(MLModel).filter(
            MLModel.market == record.market,
            MLModel.is_active == True,  # noqa: E712
        ).update({"is_active": False})

        # Activate selected model
        record.is_active = True
        db.commit()

        logger.info("Activated model %s v%s (id=%d) for market %s", record.model_name, record.model_version, model_id, record.market)

    def get_active(self, market: str, db: Session) -> MLModel | None:
        """현재 활성 모델 조회."""
        return (
            db.query(MLModel)
            .filter(
                MLModel.market == market,
                MLModel.is_active == True,  # noqa: E712
            )
            .first()
        )

    def list_models(self, market: str | None, db: Session) -> list[MLModel]:
        """모델 목록 조회."""
        query = db.query(MLModel).order_by(MLModel.created_at.desc())
        if market:
            query = query.filter(MLModel.market == market)
        return query.all()
