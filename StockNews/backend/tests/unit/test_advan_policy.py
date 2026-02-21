"""Advan Policy 관리 단위 테스트."""

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.advan.models import AdvanPolicy
from app.advan.policy import (
    create_default_policy,
    get_active_policy,
    get_default_policy,
    load_policy_params,
    save_policy_metrics,
)


class TestDefaultPolicy:
    """기본 정책 테스트."""

    def test_get_default_policy(self):
        """기본 정책 dict 생성."""
        policy = get_default_policy()
        assert "event_priors" in policy
        assert "thresholds" in policy
        assert "template_config" in policy
        assert "retrieval_config" in policy

    def test_default_priors_have_all_types(self):
        """기본 priors에 주요 이벤트 유형이 포함."""
        policy = get_default_policy()
        priors = policy["event_priors"]
        assert "실적" in priors
        assert "수주" in priors
        assert "증자" in priors

    def test_default_thresholds_valid(self):
        """기본 임계값이 유효한 범위."""
        policy = get_default_policy()
        thresholds = policy["thresholds"]
        assert 0.5 <= thresholds["buy_p"] <= 1.0
        assert 0.5 <= thresholds["sell_p"] <= 1.0
        assert thresholds["abstain_low"] < thresholds["abstain_high"]

    def test_create_default_in_db(self, db_session: Session):
        """DB에 기본 정책 생성."""
        policy = create_default_policy(db_session)
        assert policy.id is not None
        assert policy.is_active is True
        assert policy.name == "Default Policy"

        # JSON 파싱 확인
        priors = json.loads(policy.event_priors)
        assert isinstance(priors, dict)
        assert len(priors) > 0

    def test_create_default_idempotent(self, db_session: Session):
        """기본 정책 중복 생성 방지."""
        p1 = create_default_policy(db_session)
        p2 = create_default_policy(db_session)
        assert p1.id == p2.id  # 이미 있으면 기존 반환


class TestPolicyOperations:
    """정책 CRUD 테스트."""

    def test_get_active_policy(self, db_session: Session):
        """활성 정책 조회."""
        # 정책 없을 때
        assert get_active_policy(db_session) is None

        # 기본 정책 생성 후
        create_default_policy(db_session)
        active = get_active_policy(db_session)
        assert active is not None
        assert active.is_active is True

    def test_load_policy_params(self, db_session: Session):
        """정책 파라미터 로드."""
        policy = create_default_policy(db_session)
        params = load_policy_params(policy)
        assert isinstance(params, dict)
        assert "event_priors" in params
        assert "thresholds" in params
        assert isinstance(params["event_priors"], dict)
        assert isinstance(params["thresholds"], dict)

    def test_save_policy_metrics(self, db_session: Session):
        """정책 메트릭 업데이트."""
        policy = create_default_policy(db_session)
        save_policy_metrics(db_session, policy.id, brier=0.25, accuracy=0.68, calibration=0.08)

        db_session.refresh(policy)
        assert policy.latest_brier == 0.25
        assert policy.latest_accuracy == 0.68
        assert policy.latest_calibration == 0.08


class TestPolicyModel:
    """AdvanPolicy 모델 테스트."""

    def test_create_policy(self, db_session: Session):
        """정책 생성."""
        policy = AdvanPolicy(
            name="test_policy",
            version="v1.0",
            description="테스트 정책",
            is_active=False,
            event_priors=json.dumps({"실적": 0.8, "수주": 0.6}),
            thresholds=json.dumps({"buy_p": 0.62, "sell_p": 0.62}),
            template_config=json.dumps({"include_features": True}),
            retrieval_config=json.dumps({"max_results": 3}),
        )
        db_session.add(policy)
        db_session.commit()

        saved = db_session.query(AdvanPolicy).filter(AdvanPolicy.name == "test_policy").first()
        assert saved is not None
        assert saved.version == "v1.0"
        assert json.loads(saved.event_priors)["실적"] == 0.8

    def test_policy_repr(self):
        """정책 repr."""
        policy = AdvanPolicy(
            name="test", version="v1.0", is_active=True,
            event_priors="{}", thresholds="{}", template_config="{}",
            retrieval_config="{}",
        )
        assert "test" in repr(policy)
