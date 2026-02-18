"""키움 REST API 시세 조회 클라이언트"""

import logging

import httpx

from src.kiwoom_client.auth import KiwoomAuth

logger = logging.getLogger("stockagent.kiwoom.market")


class InvalidStockCodeError(Exception):
    """잘못된 종목코드 예외"""
    pass


class KiwoomMarket:
    """시세 조회: 현재가, 호가, 거래량"""

    def __init__(self, auth: KiwoomAuth, base_url: str = "https://openapi.koreainvestment.com:9443"):
        self._auth = auth
        self._base_url = base_url

    async def _get_headers(self) -> dict:
        token = await self._auth.get_token()
        return {
            "authorization": f"Bearer {token}",
            "content-type": "application/json; charset=utf-8",
        }

    async def get_price(self, stock_code: str) -> dict:
        """현재가 조회"""
        headers = await self._get_headers()
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(
                "/uapi/domestic-stock/v1/quotations/inquire-price",
                headers=headers,
                params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": stock_code},
            )

        if resp.status_code == 400:
            raise InvalidStockCodeError(f"Invalid stock code: {stock_code}")

        data = resp.json()["output"]
        return {
            "current_price": int(data["stck_prpr"]),
            "open": int(data["stck_oprc"]),
            "high": int(data["stck_hgpr"]),
            "low": int(data["stck_lwpr"]),
            "volume": int(data["acml_vol"]),
            "trade_value": int(data["acml_tr_pbmn"]),
        }

    async def get_orderbook(self, stock_code: str) -> dict:
        """호가 조회"""
        headers = await self._get_headers()
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(
                "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
                headers=headers,
                params={"fid_cond_mrkt_div_code": "J", "fid_input_iscd": stock_code},
            )

        data = resp.json()["output1"]
        asks = [int(data[f"askp{i}"]) for i in range(1, 4) if data.get(f"askp{i}")]
        bids = [int(data[f"bidp{i}"]) for i in range(1, 4) if data.get(f"bidp{i}")]
        return {"asks": asks, "bids": bids}
