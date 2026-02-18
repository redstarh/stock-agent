"""T-B3: 키움 인증 클라이언트 테스트"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import httpx
import respx


@pytest.fixture
def mock_kiwoom():
    with respx.mock(base_url="https://openapi.koreainvestment.com:9443") as mock:
        mock.post("/oauth2/tokenP").respond(json={
            "access_token": "test-token-abc123",
            "token_type": "Bearer",
            "expires_in": 86400,
        })
        yield mock


@pytest.mark.asyncio
async def test_get_token_success(mock_kiwoom):
    """정상 토큰 발급"""
    from src.kiwoom_client.auth import KiwoomAuth

    auth = KiwoomAuth(
        app_key="test-key",
        app_secret="test-secret",
        base_url="https://openapi.koreainvestment.com:9443",
    )
    token = await auth.get_token()
    assert token is not None
    assert len(token) > 0
    assert token == "test-token-abc123"


@pytest.mark.asyncio
async def test_token_caching(mock_kiwoom):
    """토큰 캐싱: 두 번째 호출은 API 재요청 없이 캐시 반환"""
    from src.kiwoom_client.auth import KiwoomAuth

    auth = KiwoomAuth(
        app_key="test-key",
        app_secret="test-secret",
        base_url="https://openapi.koreainvestment.com:9443",
    )
    token1 = await auth.get_token()
    token2 = await auth.get_token()
    assert token1 == token2
    assert mock_kiwoom.calls.call_count == 1


@pytest.mark.asyncio
async def test_token_refresh_on_expiry(mock_kiwoom):
    """만료된 토큰 자동 갱신"""
    from src.kiwoom_client.auth import KiwoomAuth

    auth = KiwoomAuth(
        app_key="test-key",
        app_secret="test-secret",
        base_url="https://openapi.koreainvestment.com:9443",
    )
    # 첫 번째 토큰 발급
    await auth.get_token()
    # 만료 시간을 과거로 설정
    auth._token_expires_at = datetime.now() - timedelta(seconds=1)
    # 재발급 되어야 함
    token = await auth.get_token()
    assert token is not None
    assert mock_kiwoom.calls.call_count == 2


@pytest.mark.asyncio
async def test_token_failure_raises(mock_kiwoom):
    """인증 실패 시 예외 발생"""
    from src.kiwoom_client.auth import KiwoomAuth, AuthenticationError

    mock_kiwoom.post("/oauth2/tokenP").respond(status_code=401, json={
        "error": "unauthorized",
    })
    auth = KiwoomAuth(
        app_key="wrong-key",
        app_secret="wrong-secret",
        base_url="https://openapi.koreainvestment.com:9443",
    )
    with pytest.raises(AuthenticationError):
        await auth.get_token()
