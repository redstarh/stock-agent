"""T-B9: Account API 통합 테스트"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from src.main import app
from src.kiwoom_client.account import KiwoomAccount


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_account():
    account = AsyncMock(spec=KiwoomAccount)
    account.get_balance.return_value = {
        "cash": 10_000_000,
        "available": 9_500_000,
    }
    account.get_positions.return_value = [
        {
            "stock_code": "005930",
            "name": "삼성전자",
            "quantity": 100,
            "avg_price": 70000.0,
            "current_price": 71000,
            "pnl": 100000,
            "pnl_rate": 1.43,
        },
    ]
    account.get_pnl.return_value = {
        "total_value": 18_350_000,
        "total_pnl": 350_000,
        "total_cost": 13_000_000,
    }
    return account


@pytest.mark.asyncio
async def test_get_balance(async_client, mock_account):
    """예수금 조회 API"""
    with patch("src.api.account.get_account_client", return_value=mock_account):
        resp = await async_client.get("/api/v1/account/balance")
    assert resp.status_code == 200
    data = resp.json()
    assert "cash" in data
    assert data["cash"] == 10_000_000


@pytest.mark.asyncio
async def test_get_positions(async_client, mock_account):
    """보유종목 조회 API"""
    with patch("src.api.account.get_account_client", return_value=mock_account):
        resp = await async_client.get("/api/v1/account/positions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["stock_code"] == "005930"


@pytest.mark.asyncio
async def test_get_pnl(async_client, mock_account):
    """평가손익 조회 API"""
    with patch("src.api.account.get_account_client", return_value=mock_account):
        resp = await async_client.get("/api/v1/account/pnl")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_pnl"] == 350_000
