"""정책 관리 — 기본 정책 생성 및 관리."""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.advan.models import AdvanPolicy
from app.advan.schemas import EventPriors, PolicyThresholds, RetrievalConfig, TemplateConfig

logger = logging.getLogger(__name__)


def get_default_policy() -> dict:
    """기본 정책 파라미터 반환.

    Returns:
        dict with event_priors, thresholds, template_config, retrieval_config
    """
    return {
        "name": "Default Policy",
        "version": "v1.0",
        "description": "기본 정책 — 보수적 임계값과 균형 잡힌 이벤트 가중치",
        "event_priors": EventPriors().model_dump(),
        "thresholds": PolicyThresholds().model_dump(),
        "template_config": TemplateConfig().model_dump(),
        "retrieval_config": RetrievalConfig().model_dump(),
    }


def create_default_policy(db: Session) -> AdvanPolicy:
    """기본 정책을 DB에 생성 (없을 경우만).

    Args:
        db: DB 세션

    Returns:
        생성된 AdvanPolicy 인스턴스
    """
    # 기본 정책이 이미 존재하는지 확인
    existing = db.query(AdvanPolicy).filter(AdvanPolicy.name == "Default Policy").first()
    if existing:
        logger.info(f"Default policy already exists: id={existing.id}")
        return existing

    default_params = get_default_policy()

    policy = AdvanPolicy(
        name=default_params["name"],
        version=default_params["version"],
        description=default_params["description"],
        is_active=True,  # 첫 정책은 활성화
        event_priors=json.dumps(default_params["event_priors"], ensure_ascii=False),
        thresholds=json.dumps(default_params["thresholds"], ensure_ascii=False),
        template_config=json.dumps(default_params["template_config"], ensure_ascii=False),
        retrieval_config=json.dumps(default_params["retrieval_config"], ensure_ascii=False),
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    logger.info(f"Created default policy: id={policy.id}")
    return policy


def get_active_policy(db: Session) -> AdvanPolicy | None:
    """현재 활성 정책 조회.

    Args:
        db: DB 세션

    Returns:
        활성 정책 또는 None
    """
    return db.query(AdvanPolicy).filter(AdvanPolicy.is_active == True).first()


def load_policy_params(policy: AdvanPolicy) -> dict:
    """AdvanPolicy의 JSON 필드를 파싱하여 구조화된 dict로 변환.

    Args:
        policy: AdvanPolicy 인스턴스

    Returns:
        {
            "event_priors": dict,
            "thresholds": dict,
            "template_config": dict,
            "retrieval_config": dict,
        }
    """
    return {
        "event_priors": json.loads(policy.event_priors),
        "thresholds": json.loads(policy.thresholds),
        "template_config": json.loads(policy.template_config),
        "retrieval_config": json.loads(policy.retrieval_config),
    }


def save_policy_metrics(
    db: Session,
    policy_id: int,
    brier: float,
    accuracy: float,
    calibration: float,
) -> None:
    """정책의 최신 메트릭 업데이트.

    Args:
        db: DB 세션
        policy_id: 정책 ID
        brier: Brier score
        accuracy: 정확도
        calibration: Calibration error
    """
    policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == policy_id).first()
    if not policy:
        logger.warning(f"Policy not found: id={policy_id}")
        return

    policy.latest_brier = brier
    policy.latest_accuracy = accuracy
    policy.latest_calibration = calibration
    policy.updated_at = datetime.now(UTC)

    db.commit()
    logger.info(f"Updated metrics for policy_id={policy_id}: brier={brier:.4f}, acc={accuracy:.4f}")
