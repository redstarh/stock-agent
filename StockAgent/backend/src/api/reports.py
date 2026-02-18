"""리포트/통계 API 라우터"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from src.core.report import ReportGenerator

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# In-memory storage for unit tests; will be replaced by DB in integration
_trade_store: list[dict] = []
_metrics_store: list[dict] = []


async def get_trades_by_date(target_date: str) -> list[dict]:
    """특정 날짜의 매매 내역 조회"""
    return [t for t in _trade_store if t["date"] == target_date]


async def get_all_metrics() -> list[dict]:
    """모든 학습 메트릭 조회"""
    return _metrics_store


@router.get("/daily")
async def get_daily_report(date_param: Optional[str] = Query(None, alias="date")):
    """일간 리포트 조회

    Args:
        date_param: 조회할 날짜 (YYYY-MM-DD). 미지정시 오늘 날짜 사용

    Returns:
        일간 매매 리포트 (총 거래수, 승률, 총 손익, 최적/최악 패턴)
    """
    target_date = date_param if date_param else str(date.today())
    trades = await get_trades_by_date(target_date)
    return ReportGenerator.daily(date=target_date, trades=trades)


@router.get("/metrics")
async def get_metrics():
    """학습 메트릭 목록 조회

    Returns:
        학습 메트릭 목록 (승률, 총 손익 등)
    """
    return await get_all_metrics()
