"""Strategy 관리 API 라우터"""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])

# In-memory storage for unit tests; will be replaced by DB/Redis in integration
_strategy_config = {"top_n": 5, "news_threshold": 70, "volume_rank_limit": 100}
_strategy_enabled = True


class StrategyConfigUpdate(BaseModel):
    """전략 설정 업데이트 요청"""

    top_n: int = Field(ge=1, le=100, description="거래대금 상위 N개")
    news_threshold: int = Field(ge=0, le=100, description="뉴스 점수 임계값")


class StrategyToggle(BaseModel):
    """전략 활성화/비활성화 요청"""

    enabled: bool


@router.get("/config")
async def get_strategy_config() -> dict:
    """현재 전략 설정 조회"""
    return _strategy_config.copy()


@router.put("/config")
async def update_strategy_config(config: StrategyConfigUpdate) -> dict:
    """전략 설정 업데이트"""
    _strategy_config["top_n"] = config.top_n
    _strategy_config["news_threshold"] = config.news_threshold
    return _strategy_config.copy()


@router.post("/toggle")
async def toggle_strategy(toggle: StrategyToggle) -> dict:
    """전략 활성화/비활성화"""
    global _strategy_enabled
    _strategy_enabled = toggle.enabled
    return {"enabled": _strategy_enabled}
