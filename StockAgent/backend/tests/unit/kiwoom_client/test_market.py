"""T-B4: 키움 시세 클라이언트 테스트"""

import pytest
import respx
from unittest.mock import AsyncMock

from src.kiwoom_client.auth import KiwoomAuth
from src.kiwoom_client.market import KiwoomMarket, InvalidStockCodeError


@pytest.fixture
def mock_auth():
    auth = AsyncMock(spec=KiwoomAuth)
    auth.get_token.return_value = "test-token"
    return auth


@pytest.fixture
def mock_kiwoom():
    with respx.mock(base_url="https://openapi.koreainvestment.com:9443", assert_all_called=False) as mock:
        mock.get("/uapi/domestic-stock/v1/quotations/inquire-price").respond(json={
            "output": {
                "stck_prpr": "71000",
                "stck_oprc": "70000",
                "stck_hgpr": "72000",
                "stck_lwpr": "69500",
                "acml_vol": "12345678",
                "acml_tr_pbmn": "876543210000",
            }
        })
        mock.get("/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn").respond(json={
            "output1": {
                "askp1": "71100", "askp2": "71200", "askp3": "71300",
                "bidp1": "70900", "bidp2": "70800", "bidp3": "70700",
            }
        })
        yield mock


@pytest.mark.asyncio
async def test_get_price(mock_auth, mock_kiwoom):
    """현재가 조회"""
    market = KiwoomMarket(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    price = await market.get_price("005930")
    assert price["current_price"] == 71000
    assert price["open"] == 70000
    assert price["high"] == 72000
    assert price["low"] == 69500


@pytest.mark.asyncio
async def test_get_orderbook(mock_auth, mock_kiwoom):
    """호가 조회"""
    market = KiwoomMarket(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    book = await market.get_orderbook("005930")
    assert "asks" in book and "bids" in book
    assert len(book["asks"]) > 0
    assert len(book["bids"]) > 0


@pytest.mark.asyncio
async def test_get_volume(mock_auth, mock_kiwoom):
    """거래량/거래대금 조회"""
    market = KiwoomMarket(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    price = await market.get_price("005930")
    assert price["volume"] >= 0
    assert price["trade_value"] >= 0


@pytest.mark.asyncio
async def test_invalid_stock_code(mock_auth):
    """잘못된 종목코드 에러 처리"""
    with respx.mock(base_url="https://openapi.koreainvestment.com:9443") as mock:
        mock.get("/uapi/domestic-stock/v1/quotations/inquire-price").respond(
            status_code=400, json={"msg1": "잘못된 종목코드"}
        )
        market = KiwoomMarket(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
        with pytest.raises(InvalidStockCodeError):
            await market.get_price("INVALID")
