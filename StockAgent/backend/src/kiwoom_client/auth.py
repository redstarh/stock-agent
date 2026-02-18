"""키움 REST API 인증 토큰 관리"""

import logging
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger("stockagent.kiwoom.auth")


class AuthenticationError(Exception):
    """인증 실패 예외"""
    pass


class KiwoomAuth:
    """OAuth 토큰 발급/갱신/캐싱"""

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str = "https://openapi.koreainvestment.com:9443",
    ):
        self._app_key = app_key
        self._app_secret = app_secret
        self._base_url = base_url
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    async def get_token(self) -> str:
        """토큰 반환 (캐시 유효하면 캐시, 아니면 재발급)"""
        if self._token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._token

        await self._request_token()
        return self._token

    async def _request_token(self) -> None:
        """키움 API에 토큰 발급 요청"""
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            resp = await client.post(
                "/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self._app_key,
                    "appsecret": self._app_secret,
                },
            )

        if resp.status_code != 200:
            logger.error("토큰 발급 실패: status=%d", resp.status_code)
            raise AuthenticationError(
                f"Token request failed with status {resp.status_code}"
            )

        data = resp.json()
        self._token = data["access_token"]
        expires_in = data.get("expires_in", 86400)
        # 만료 10분 전에 갱신하도록 여유 시간 확보
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 600)
        logger.info("토큰 발급 완료 (만료: %s)", self._token_expires_at)
