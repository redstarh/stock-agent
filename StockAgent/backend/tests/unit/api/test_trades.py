"""T-B16: 매매 내역 API 테스트"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app
from src.api.trades import _trade_store


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


# Tests that exercise actual function bodies (no mocks)
@pytest.fixture
def setup_trade_store():
    """Setup and teardown for _trade_store"""
    _trade_store.clear()
    yield
    _trade_store.clear()


def test_get_trades_uses_trade_store(client, setup_trade_store):
    """매매 내역 조회 - _trade_store 직접 조작"""
    _trade_store.append({
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
    })
    _trade_store.append({
        "trade_id": "t2",
        "date": "2026-01-16",
        "stock_code": "000660",
        "stock_name": "SK하이닉스",
        "side": "sell",
        "entry_price": 120000,
        "exit_price": 122000,
        "quantity": 5,
        "pnl": 10000,
        "pnl_pct": 1.67,
        "strategy_tag": "momentum",
        "created_at": "2026-01-16T10:00:00",
    })

    resp = client.get("/api/v1/trades?page=1&size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["size"] == 10


def test_get_trades_pagination(client, setup_trade_store):
    """페이지네이션 - 10개 이상 데이터"""
    for i in range(15):
        _trade_store.append({
            "trade_id": f"t{i}",
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
        })

    # Page 1
    resp = client.get("/api/v1/trades?page=1&size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 15
    assert len(data["items"]) == 10
    assert data["page"] == 1

    # Page 2
    resp = client.get("/api/v1/trades?page=2&size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 15
    assert len(data["items"]) == 5
    assert data["page"] == 2


def test_get_trades_date_from_filter(client, setup_trade_store):
    """date_from 필터 테스트"""
    _trade_store.append({
        "trade_id": "t1",
        "date": "2026-01-10",
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "side": "buy",
        "entry_price": 70000,
        "exit_price": 71000,
        "quantity": 10,
        "pnl": 10000,
        "pnl_pct": 1.43,
        "strategy_tag": "volume_leader",
        "created_at": "2026-01-10T09:30:00",
    })
    _trade_store.append({
        "trade_id": "t2",
        "date": "2026-01-20",
        "stock_code": "000660",
        "stock_name": "SK하이닉스",
        "side": "sell",
        "entry_price": 120000,
        "exit_price": 122000,
        "quantity": 5,
        "pnl": 10000,
        "pnl_pct": 1.67,
        "strategy_tag": "momentum",
        "created_at": "2026-01-20T10:00:00",
    })

    resp = client.get("/api/v1/trades?date_from=2026-01-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["trade_id"] == "t2"


def test_get_trades_date_to_filter(client, setup_trade_store):
    """date_to 필터 테스트"""
    _trade_store.append({
        "trade_id": "t1",
        "date": "2026-01-10",
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "side": "buy",
        "entry_price": 70000,
        "exit_price": 71000,
        "quantity": 10,
        "pnl": 10000,
        "pnl_pct": 1.43,
        "strategy_tag": "volume_leader",
        "created_at": "2026-01-10T09:30:00",
    })
    _trade_store.append({
        "trade_id": "t2",
        "date": "2026-01-20",
        "stock_code": "000660",
        "stock_name": "SK하이닉스",
        "side": "sell",
        "entry_price": 120000,
        "exit_price": 122000,
        "quantity": 5,
        "pnl": 10000,
        "pnl_pct": 1.67,
        "strategy_tag": "momentum",
        "created_at": "2026-01-20T10:00:00",
    })

    resp = client.get("/api/v1/trades?date_to=2026-01-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["trade_id"] == "t1"


def test_get_trade_by_id_from_store(client, setup_trade_store):
    """매매 상세 조회 - _trade_store 직접 조작"""
    _trade_store.append({
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
    })

    resp = client.get("/api/v1/trades/t1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trade_id"] == "t1"
    assert data["stock_code"] == "005930"


def test_get_trade_not_found_from_store(client, setup_trade_store):
    """존재하지 않는 매매 조회 - _trade_store 비어있음"""
    resp = client.get("/api/v1/trades/nonexistent")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Trade not found"
