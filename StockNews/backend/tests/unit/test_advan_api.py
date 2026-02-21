"""Advan API 엔드포인트 단위 테스트."""

import json
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.advan.api import router
from app.advan.models import AdvanEvent, AdvanPolicy, AdvanSimulationRun
from app.core.database import get_db


@pytest.fixture
def test_app(db_session: Session):
    """테스트 앱 생성."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    """테스트 클라이언트."""
    return TestClient(test_app)


@pytest.fixture
def sample_policy(db_session: Session):
    """테스트용 정책 생성."""
    policy = AdvanPolicy(
        name="test_default",
        version="v1.0",
        description="테스트 기본 정책",
        is_active=True,
        event_priors=json.dumps({"실적": 0.8, "수주": 0.6, "증자": 0.5}),
        thresholds=json.dumps({"buy_p": 0.62, "sell_p": 0.62, "abstain_low": 0.4, "abstain_high": 0.6, "label_threshold_pct": 2.0}),
        template_config=json.dumps({"include_features": True, "include_similar_events": True, "max_events_per_stock": 5}),
        retrieval_config=json.dumps({"max_results": 3, "lookback_days": 365, "similarity_threshold": 0.5}),
    )
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)
    return policy


@pytest.fixture
def sample_events(db_session: Session):
    """테스트용 이벤트 생성."""
    events = [
        AdvanEvent(
            ticker="005930", stock_name="삼성전자", market="KR",
            event_type="실적", direction="positive",
            magnitude=0.8, novelty=0.9, credibility=0.95,
            is_disclosure=True, title="삼성전자 4분기 실적",
            source="DART", event_timestamp=datetime(2024, 1, 15, 9, 0, tzinfo=UTC),
        ),
        AdvanEvent(
            ticker="000660", stock_name="SK하이닉스", market="KR",
            event_type="수주", direction="positive",
            magnitude=0.6, novelty=0.7, credibility=0.6,
            is_disclosure=False, title="SK하이닉스 대규모 수주",
            source="Naver", event_timestamp=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        ),
    ]
    for e in events:
        db_session.add(e)
    db_session.commit()
    return events


class TestEventAPI:
    """이벤트 API 테스트."""

    def test_list_events(self, client, sample_events):
        resp = client.get("/api/v1/advan/events?market=KR")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["events"]) == 2

    def test_list_events_filter_type(self, client, sample_events):
        resp = client.get("/api/v1/advan/events?market=KR&event_type=실적")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["events"][0]["event_type"] == "실적"

    def test_list_events_filter_ticker(self, client, sample_events):
        resp = client.get("/api/v1/advan/events?market=KR&ticker=005930")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    def test_list_events_empty(self, client):
        resp = client.get("/api/v1/advan/events?market=US")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestPolicyAPI:
    """정책 API 테스트."""

    def test_list_policies(self, client, sample_policy):
        resp = client.get("/api/v1/advan/policies")
        assert resp.status_code == 200
        policies = resp.json()
        assert len(policies) >= 1
        assert policies[0]["name"] == "test_default"

    def test_create_policy(self, client):
        resp = client.post("/api/v1/advan/policies", json={
            "name": "new_policy",
            "version": "v2.0",
            "description": "새 정책",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "new_policy"
        assert data["version"] == "v2.0"
        assert data["is_active"] is False

    def test_get_policy(self, client, sample_policy):
        resp = client.get(f"/api/v1/advan/policies/{sample_policy.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test_default"
        assert "event_priors" in data

    def test_get_policy_not_found(self, client):
        resp = client.get("/api/v1/advan/policies/99999")
        assert resp.status_code == 404

    def test_update_policy(self, client, sample_policy):
        resp = client.put(f"/api/v1/advan/policies/{sample_policy.id}", json={
            "name": "updated_policy",
            "version": "v1.1",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "updated_policy"

    def test_delete_inactive_policy(self, client, db_session):
        """비활성 정책 삭제 가능."""
        policy = AdvanPolicy(
            name="to_delete", version="v1.0", is_active=False,
            event_priors="{}", thresholds="{}", template_config="{}",
            retrieval_config="{}",
        )
        db_session.add(policy)
        db_session.commit()
        db_session.refresh(policy)

        resp = client.delete(f"/api/v1/advan/policies/{policy.id}")
        assert resp.status_code == 200

    def test_delete_active_policy_fails(self, client, sample_policy):
        """활성 정책은 삭제 불가."""
        resp = client.delete(f"/api/v1/advan/policies/{sample_policy.id}")
        assert resp.status_code == 400

    def test_create_default_policy(self, client):
        resp = client.post("/api/v1/advan/policies/default")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Default Policy"


class TestRunAPI:
    """시뮬레이션 실행 API 테스트."""

    def test_list_runs_empty(self, client):
        resp = client.get("/api/v1/advan/runs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_run_invalid_policy(self, client):
        resp = client.post("/api/v1/advan/runs", json={
            "name": "test_run",
            "policy_id": 99999,
            "market": "KR",
            "horizon": 3,
            "label_threshold_pct": 2.0,
            "date_from": "2024-01-01",
            "date_to": "2024-01-31",
        })
        assert resp.status_code == 404

    def test_delete_run_not_found(self, client):
        resp = client.delete("/api/v1/advan/runs/99999")
        assert resp.status_code == 404


class TestCompareAPI:
    """비교 API 테스트."""

    def test_compare_requires_two_ids(self, client):
        resp = client.get("/api/v1/advan/compare?run_ids=1")
        assert resp.status_code == 400

    def test_compare_not_found(self, client):
        resp = client.get("/api/v1/advan/compare?run_ids=99998,99999")
        assert resp.status_code == 404


class TestEvaluateAPI:
    """평가 API 테스트."""

    def test_evaluate_not_found(self, client):
        resp = client.get("/api/v1/advan/evaluate/99999")
        assert resp.status_code == 404

    def test_guardrails_not_found(self, client):
        resp = client.get("/api/v1/advan/guardrails/99999")
        assert resp.status_code == 404
