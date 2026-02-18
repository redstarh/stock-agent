"""매매 내역 API 라우터"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/trades", tags=["trades"])

# In-memory storage for unit tests; will be replaced by DB in integration
_trade_store: list[dict] = []


async def get_trades(
    page: int = 1,
    size: int = 10,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    """매매 내역 조회 (페이지네이션 + 날짜 필터)"""
    filtered = _trade_store
    if date_from:
        filtered = [t for t in filtered if t["date"] >= str(date_from)]
    if date_to:
        filtered = [t for t in filtered if t["date"] <= str(date_to)]

    total = len(filtered)
    start = (page - 1) * size
    items = filtered[start:start + size]
    return {"items": items, "total": total, "page": page, "size": size}


async def get_trade_by_id(trade_id: str) -> Optional[dict]:
    """개별 매매 조회"""
    for t in _trade_store:
        if t["trade_id"] == trade_id:
            return t
    return None


@router.get("")
async def list_trades(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """매매 내역 목록"""
    return await get_trades(page=page, size=size, date_from=date_from, date_to=date_to)


@router.get("/{trade_id}")
async def trade_detail(trade_id: str):
    """매매 상세"""
    trade = await get_trade_by_id(trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade
