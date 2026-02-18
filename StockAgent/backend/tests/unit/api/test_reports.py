"""T-B22: 리포트/통계 API 테스트"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_trades():
    return [
        {
            "trade_id": "t1",
            "date": "2026-01-15",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "side": "buy",
            "entry_price": 70000,
            "exit_price": 71000,
            "quantity": 10,
            "pnl": 10000,
            "pnl_pct": 1.43,
            "strategy_tag": "volume_leader",
        },
        {
            "trade_id": "t2",
            "date": "2026-01-15",
            "stock_code": "000660",
            "stock_name": "SK하이닉스",
            "side": "buy",
            "entry_price": 120000,
            "exit_price": 118000,
            "quantity": 5,
            "pnl": -10000,
            "pnl_pct": -1.67,
            "strategy_tag": "news_spike",
        },
    ]


@pytest.fixture
def mock_learning_metrics():
    return [
        {
            "id": 1,
            "date": "2026-01-15",
            "metric_type": "win_rate",
            "value": 50.0,
            "strategy_tag": "volume_leader",
        },
        {
            "id": 2,
            "date": "2026-01-15",
            "metric_type": "total_pnl",
            "value": 0.0,
            "strategy_tag": "all",
        },
    ]


def test_get_daily_report(client, mock_trades):
    """일간 리포트 조회"""
    with patch("src.api.reports.get_trades_by_date") as mock_fn:
        mock_fn.return_value = mock_trades
        resp = client.get("/api/v1/reports/daily?date=2026-01-15")
        assert resp.status_code == 200
        data = resp.json()
        assert "win_rate" in data
        assert "total_trades" in data
        assert "total_pnl" in data
        assert "date" in data
        assert data["date"] == "2026-01-15"
        assert data["total_trades"] == 2
        assert data["win_rate"] == 50.0


def test_get_daily_report_no_date(client):
    """날짜 파라미터 없이 일간 리포트 조회 (오늘 날짜 기본값)"""
    with patch("src.api.reports.get_trades_by_date") as mock_fn:
        mock_fn.return_value = []
        resp = client.get("/api/v1/reports/daily")
        assert resp.status_code == 200
        data = resp.json()
        assert "date" in data
        assert "total_trades" in data
        assert data["total_trades"] == 0


def test_get_metrics(client, mock_learning_metrics):
    """학습 메트릭 목록 조회"""
    with patch("src.api.reports.get_all_metrics") as mock_fn:
        mock_fn.return_value = mock_learning_metrics
        resp = client.get("/api/v1/reports/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["metric_type"] == "win_rate"


def test_get_metrics_empty(client):
    """학습 메트릭 없을 때"""
    with patch("src.api.reports.get_all_metrics") as mock_fn:
        mock_fn.return_value = []
        resp = client.get("/api/v1/reports/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0
