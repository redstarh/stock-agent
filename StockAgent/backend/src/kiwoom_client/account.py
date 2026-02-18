"""키움 REST API 계좌 클라이언트"""

import logging

import httpx

from src.kiwoom_client.auth import KiwoomAuth

logger = logging.getLogger("stockagent.kiwoom.account")


class KiwoomAccount:
    """계좌 정보: 예수금, 보유종목, 평가손익"""

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

    async def get_balance(self) -> dict:
        """예수금 조회"""
        headers = await self._get_headers(tr_id="TTTC8908R")
        params = {
            "CANO": "00000000",
            "ACNT_PRDT_CD": "01",
            "PDNO": "",
            "ORD_UNPR": "",
            "ORD_DVSN": "02",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "N",
        }

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(
                "/uapi/domestic-stock/v1/trading/inquire-psbl-order",
                headers=headers,
                params=params,
            )

        data = resp.json()
        output = data.get("output", {})
        return {
            "cash": int(output.get("dnca_tot_amt", 0)),
            "available": int(output.get("nxdy_excc_amt", 0)),
        }

    async def get_positions(self) -> list[dict]:
        """보유종목 리스트"""
        headers = await self._get_headers(tr_id="TTTC8434R")
        params = {
            "CANO": "00000000",
            "ACNT_PRDT_CD": "01",
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(
                "/uapi/domestic-stock/v1/trading/inquire-balance",
                headers=headers,
                params=params,
            )

        data = resp.json()
        positions = []
        for item in data.get("output1", []):
            positions.append({
                "stock_code": item["pdno"],
                "name": item.get("prdt_name", ""),
                "quantity": int(item["hldg_qty"]),
                "avg_price": float(item["pchs_avg_pric"]),
                "current_price": int(item["prpr"]),
                "pnl": int(item["evlu_pfls_amt"]),
                "pnl_rate": float(item["evlu_pfls_rt"]),
            })
        return positions

    async def get_pnl(self) -> dict:
        """평가손익 조회"""
        headers = await self._get_headers(tr_id="TTTC8434R")
        params = {
            "CANO": "00000000",
            "ACNT_PRDT_CD": "01",
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.get(
                "/uapi/domestic-stock/v1/trading/inquire-balance",
                headers=headers,
                params=params,
            )

        data = resp.json()
        summary = data.get("output2", [{}])[0]
        return {
            "total_value": int(summary.get("tot_evlu_amt", 0)),
            "total_pnl": int(summary.get("tot_evlu_pfls_amt", 0)),
            "total_cost": int(summary.get("pchs_amt_smtl_amt", 0)),
        }
