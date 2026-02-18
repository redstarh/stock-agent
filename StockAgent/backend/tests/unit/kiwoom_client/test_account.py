"""T-B6: 키움 계좌 클라이언트 테스트"""

import pytest
import respx
from unittest.mock import AsyncMock

from src.kiwoom_client.auth import KiwoomAuth
from src.kiwoom_client.account import KiwoomAccount


@pytest.fixture
def mock_auth():
    auth = AsyncMock(spec=KiwoomAuth)
    auth.get_token.return_value = "test-token"
    return auth


@pytest.fixture
def mock_kiwoom():
    with respx.mock(base_url="https://openapi.koreainvestment.com:9443", assert_all_called=False) as mock:
        mock.get("/uapi/domestic-stock/v1/trading/inquire-psbl-order").respond(json={
            "output": {
                "dnca_tot_amt": "10000000",
                "nxdy_excc_amt": "9500000",
                "prvs_rcdl_excc_amt": "9500000",
            },
            "rt_cd": "0",
        })
        mock.get("/uapi/domestic-stock/v1/trading/inquire-balance").respond(json={
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "100",
                    "pchs_avg_pric": "70000.00",
                    "prpr": "71000",
                    "evlu_pfls_amt": "100000",
                    "evlu_pfls_rt": "1.43",
                },
                {
                    "pdno": "000660",
                    "prdt_name": "SK하이닉스",
                    "hldg_qty": "50",
                    "pchs_avg_pric": "120000.00",
                    "prpr": "125000",
                    "evlu_pfls_amt": "250000",
                    "evlu_pfls_rt": "4.17",
                },
            ],
            "output2": [
                {
                    "tot_evlu_amt": "18350000",
                    "tot_evlu_pfls_amt": "350000",
                    "pchs_amt_smtl_amt": "13000000",
                },
            ],
            "rt_cd": "0",
        })
        yield mock


@pytest.mark.asyncio
async def test_get_balance(mock_auth, mock_kiwoom):
    """예수금 조회"""
    account = KiwoomAccount(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    balance = await account.get_balance()
    assert "cash" in balance
    assert balance["cash"] >= 0
    assert balance["cash"] == 10_000_000


@pytest.mark.asyncio
async def test_get_positions(mock_auth, mock_kiwoom):
    """보유종목 리스트"""
    account = KiwoomAccount(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    positions = await account.get_positions()
    assert isinstance(positions, list)
    assert len(positions) == 2
    assert positions[0]["stock_code"] == "005930"
    assert positions[0]["quantity"] == 100


@pytest.mark.asyncio
async def test_get_pnl(mock_auth, mock_kiwoom):
    """평가손익 조회"""
    account = KiwoomAccount(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    pnl = await account.get_pnl()
    assert "total_value" in pnl
    assert "total_pnl" in pnl
    assert pnl["total_pnl"] == 350_000


@pytest.mark.asyncio
async def test_empty_positions(mock_auth):
    """보유종목 없을 때 빈 리스트"""
    with respx.mock(base_url="https://openapi.koreainvestment.com:9443") as mock:
        mock.get("/uapi/domestic-stock/v1/trading/inquire-balance").respond(json={
            "output1": [],
            "output2": [{"tot_evlu_amt": "0", "tot_evlu_pfls_amt": "0", "pchs_amt_smtl_amt": "0"}],
            "rt_cd": "0",
        })
        account = KiwoomAccount(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
        positions = await account.get_positions()
        assert positions == []
