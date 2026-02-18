"""키움 REST API 주문 클라이언트"""

import logging

import httpx

from src.kiwoom_client.auth import KiwoomAuth

logger = logging.getLogger("stockagent.kiwoom.order")


class KiwoomOrder:
    """매수/매도 주문, 취소, 체결 조회"""

    def __init__(self, auth: KiwoomAuth, base_url: str = "https://openapi.koreainvestment.com:9443"):
        self._auth = auth
        self._base_url = base_url

    async def _get_headers(self, tr_id: str) -> dict:
        token = await self._auth.get_token()
        return {
            "authorization": f"Bearer {token}",
            "content-type": "application/json; charset=utf-8",
            "tr_id": tr_id,
        }

    async def buy(self, stock_code: str, qty: int, price: int) -> dict:
        """매수 주문"""
        if qty <= 0:
            raise ValueError(f"주문 수량은 1 이상이어야 합니다: {qty}")

        return await self._place_order(
            stock_code=stock_code,
            qty=qty,
            price=price,
            tr_id="TTTC0802U",  # 매수
            side="buy",
        )

    async def sell(self, stock_code: str, qty: int, price: int) -> dict:
        """매도 주문"""
        if qty <= 0:
            raise ValueError(f"주문 수량은 1 이상이어야 합니다: {qty}")

        return await self._place_order(
            stock_code=stock_code,
            qty=qty,
            price=price,
            tr_id="TTTC0801U",  # 매도
            side="sell",
        )

    async def cancel(self, order_id: str, stock_code: str, qty: int) -> dict:
        """주문 취소"""
        headers = await self._get_headers(tr_id="TTTC0803U")  # 정정/취소
        body = {
            "CANO": "00000000",
            "ACNT_PRDT_CD": "01",
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_id,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": "02",  # 취소
            "ORD_QTY": str(qty),
            "ORD_UNPR": "0",
            "QTY_ALL_ORD_YN": "Y",
        }

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post(
                "/uapi/domestic-stock/v1/trading/order-cash",
                headers=headers,
                json=body,
            )

        data = resp.json()
        if data.get("rt_cd") != "0":
            logger.error("주문 취소 실패: %s", data.get("msg1"))
            return {"status": "failed", "message": data.get("msg1", "")}

        return {
            "status": "cancelled",
            "order_id": data["output"]["ODNO"],
        }

    async def get_status(self, order_id: str) -> dict:
        """체결 상태 조회"""
        headers = await self._get_headers(tr_id="TTTC8001R")
        params = {
            "CANO": "00000000",
            "ACNT_PRDT_CD": "01",
            "INQR_STRT_DT": "",
            "INQR_END_DT": "",
            "SLL_BUY_DVSN_CD": "00",
            "INQR_DVSN": "00",
            "PDNO": "",
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": order_id,
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(
                "/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
                headers=headers,
                params=params,
            )

        data = resp.json()
        output = data.get("output1", {})
        raw_status = output.get("ord_stts", "pending")

        status_map = {
            "filled": "filled",
            "cancelled": "cancelled",
            "failed": "failed",
        }
        mapped = status_map.get(raw_status, "pending")

        return {
            "status": mapped,
            "order_id": output.get("odno", order_id),
            "quantity": int(output.get("ord_qty", 0)),
            "filled_quantity": int(output.get("tot_ccld_qty", 0)),
        }

    async def _place_order(self, stock_code: str, qty: int, price: int, tr_id: str, side: str) -> dict:
        """주문 공통 처리"""
        headers = await self._get_headers(tr_id=tr_id)
        body = {
            "CANO": "00000000",
            "ACNT_PRDT_CD": "01",
            "PDNO": stock_code,
            "ORD_DVSN": "00",  # 지정가
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price),
        }

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post(
                "/uapi/domestic-stock/v1/trading/order-cash",
                headers=headers,
                json=body,
            )

        data = resp.json()
        if data.get("rt_cd") != "0":
            logger.error("%s 주문 실패: %s", side, data.get("msg1"))
            return {"status": "failed", "message": data.get("msg1", "")}

        output = data["output"]
        logger.info(
            "%s 주문 완료: code=%s, qty=%d, price=%d, order_id=%s",
            side, stock_code, qty, price, output["ODNO"],
        )
        return {
            "status": "submitted",
            "order_id": output["ODNO"],
            "order_time": output.get("ORD_TMD", ""),
        }
