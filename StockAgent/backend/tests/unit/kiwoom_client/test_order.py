"""T-B5: 키움 주문 클라이언트 테스트"""

import pytest
import respx
from unittest.mock import AsyncMock

from src.kiwoom_client.auth import KiwoomAuth
from src.kiwoom_client.order import KiwoomOrder


@pytest.fixture
def mock_auth():
    auth = AsyncMock(spec=KiwoomAuth)
    auth.get_token.return_value = "test-token"
    return auth


@pytest.fixture
def mock_kiwoom():
    with respx.mock(base_url="https://openapi.koreainvestment.com:9443", assert_all_called=False) as mock:
        mock.post("/uapi/domestic-stock/v1/trading/order-cash").respond(json={
            "output": {
                "KRX_FWDG_ORD_ORGNO": "00950",
                "ODNO": "0000123456",
                "ORD_TMD": "131130",
            },
            "rt_cd": "0",
            "msg_cd": "APBK0013",
            "msg1": "주문 전송 완료",
        })
        mock.get("/uapi/domestic-stock/v1/trading/inquire-daily-ccld").respond(json={
            "output1": {
                "ord_dt": "20260218",
                "odno": "ORD001",
                "sll_buy_dvsn_cd": "02",
                "ord_qty": "10",
                "ord_unpr": "70000",
                "tot_ccld_qty": "10",
                "avg_prvs": "70000",
                "ord_stts": "filled",
            },
            "rt_cd": "0",
        })
        yield mock


@pytest.mark.asyncio
async def test_buy_order(mock_auth, mock_kiwoom):
    """매수 주문 생성"""
    order = KiwoomOrder(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    result = await order.buy("005930", qty=10, price=70000)
    assert result["order_id"] is not None
    assert result["status"] == "submitted"


@pytest.mark.asyncio
async def test_sell_order(mock_auth, mock_kiwoom):
    """매도 주문 생성"""
    order = KiwoomOrder(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    result = await order.sell("005930", qty=10, price=71000)
    assert result["status"] == "submitted"


@pytest.mark.asyncio
async def test_cancel_order(mock_auth):
    """주문 취소"""
    with respx.mock(base_url="https://openapi.koreainvestment.com:9443") as mock:
        mock.post("/uapi/domestic-stock/v1/trading/order-cash").respond(json={
            "output": {
                "KRX_FWDG_ORD_ORGNO": "00950",
                "ODNO": "0000123456",
                "ORD_TMD": "131200",
            },
            "rt_cd": "0",
            "msg1": "주문 취소 완료",
        })
        order = KiwoomOrder(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
        result = await order.cancel(order_id="ORD001", stock_code="005930", qty=10)
        assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_order_status_query(mock_auth, mock_kiwoom):
    """체결 상태 조회"""
    order = KiwoomOrder(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    status = await order.get_status(order_id="ORD001")
    assert status["status"] in ("pending", "filled", "cancelled", "failed")


@pytest.mark.asyncio
async def test_order_zero_quantity_rejected(mock_auth):
    """수량 0 주문 거부"""
    order = KiwoomOrder(auth=mock_auth, base_url="https://openapi.koreainvestment.com:9443")
    with pytest.raises(ValueError):
        await order.buy("005930", qty=0, price=70000)
