"""Scanner API 라우터"""

from fastapi import APIRouter, Query

from src.core.scanner import Scanner

router = APIRouter(prefix="/api/v1/scanner", tags=["scanner"])


@router.get("/top")
async def get_top_stocks(
    top_n: int = Query(default=10, ge=1, le=100, description="상위 N개 종목"),
):
    """거래대금 상위 종목 조회

    Args:
        top_n: 조회할 상위 종목 개수 (1~100)

    Returns:
        거래대금 기준 상위 N개 종목 리스트
    """
    # TODO: 실제 구현에서는 MarketDataCollector를 통해 실시간 데이터 수집
    # 현재는 API 구조만 정의
    stocks = []
    ranked = Scanner.rank_by_trade_value(stocks, top_n=top_n)
    return {"stocks": ranked, "count": len(ranked)}
