"""T-B16: 매매 내역 API 테스트"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
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
            "created_at": "2026-01-15T09:30:00",
        }
    ]


def test_get_trades(client, mock_trades):
    """매매 내역 조회 (페이지네이션)"""
    with patch("src.api.trades.get_trades") as mock_fn:
        mock_fn.return_value = {"items": mock_trades, "total": 1, "page": 1, "size": 10}
        resp = client.get("/api/v1/trades?page=1&size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 10


def test_get_trades_filter_by_date(client, mock_trades):
    """날짜 필터"""
    with patch("src.api.trades.get_trades") as mock_fn:
        mock_fn.return_value = {"items": mock_trades, "total": 1, "page": 1, "size": 10}
        resp = client.get("/api/v1/trades?date_from=2026-01-01&date_to=2026-01-31")
        assert resp.status_code == 200


def test_get_trade_detail(client, mock_trades):
    """매매 상세 조회"""
    with patch("src.api.trades.get_trade_by_id") as mock_fn:
        mock_fn.return_value = mock_trades[0]
        resp = client.get("/api/v1/trades/t1")
        assert resp.status_code == 200
        assert resp.json()["trade_id"] == "t1"


def test_get_trade_not_found(client):
    """존재하지 않는 매매 조회"""
    with patch("src.api.trades.get_trade_by_id") as mock_fn:
        mock_fn.return_value = None
        resp = client.get("/api/v1/trades/nonexistent")
        assert resp.status_code == 404
