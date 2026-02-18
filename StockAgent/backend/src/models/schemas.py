"""Pydantic 요청/응답 스키마"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class TradeLogResponse(BaseModel):
    trade_id: str = Field(..., min_length=1)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    stock_code: str = Field(..., min_length=1)
    stock_name: str = ""
    side: str = ""
    entry_price: float = Field(..., ge=0)
    exit_price: Optional[float] = None
    quantity: int = 0
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    news_score: Optional[int] = None
    volume_rank: Optional[int] = None
    strategy_tag: Optional[str] = None


class PositionResponse(BaseModel):
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float


class AccountBalanceResponse(BaseModel):
    cash: float
    total_eval: float
    daily_pnl: float


class OrderResponse(BaseModel):
    order_id: str
    stock_code: str
    side: str
    order_type: str
    quantity: int
    price: float
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    status: str = "pending"
    kiwoom_order_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
