"""계좌 API 라우터"""

from fastapi import APIRouter

from src.config import Settings
from src.kiwoom_client.auth import KiwoomAuth
from src.kiwoom_client.account import KiwoomAccount

router = APIRouter(prefix="/api/v1/account", tags=["account"])

_account_client: KiwoomAccount | None = None


def get_account_client() -> KiwoomAccount:
    """계좌 클라이언트 싱글턴"""
    global _account_client
    if _account_client is None:
        settings = Settings()
        auth = KiwoomAuth(
            app_key=settings.KIWOOM_APP_KEY,
            app_secret=settings.KIWOOM_APP_SECRET,
            base_url=settings.KIWOOM_BASE_URL,
        )
        _account_client = KiwoomAccount(auth=auth, base_url=settings.KIWOOM_BASE_URL)
    return _account_client


@router.get("/balance")
async def get_balance():
    """예수금 조회"""
    client = get_account_client()
    return await client.get_balance()


@router.get("/positions")
async def get_positions():
    """보유종목 조회"""
    client = get_account_client()
    return await client.get_positions()


@router.get("/pnl")
async def get_pnl():
    """평가손익 조회"""
    client = get_account_client()
    return await client.get_pnl()
