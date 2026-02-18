"""SQLAlchemy ORM 모델 (v1.0 섹션 9 DB 설계 기준)"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Date, DateTime, Numeric, Boolean, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TradeLog(Base):
    __tablename__ = "trade_log"

    trade_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False)
    market = Column(String(4), default="KR")
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(50), nullable=False)
    side = Column(String(4), nullable=False)  # buy / sell
    entry_time = Column(DateTime, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    entry_price = Column(Numeric(12, 2), nullable=False)
    exit_price = Column(Numeric(12, 2), nullable=True)
    quantity = Column(Integer, nullable=False)
    pnl = Column(Numeric(12, 2), nullable=True)
    pnl_pct = Column(Numeric(8, 4), nullable=True)
    news_score = Column(Integer, nullable=True)
    volume_rank = Column(Integer, nullable=True)
    strategy_tag = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningMetrics(Base):
    __tablename__ = "learning_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    total_trades = Column(Integer, default=0)
    win_count = Column(Integer, default=0)
    win_rate = Column(Numeric(6, 2), nullable=True)
    avg_return = Column(Numeric(8, 4), nullable=True)
    max_drawdown = Column(Numeric(8, 4), nullable=True)
    total_pnl = Column(Numeric(12, 2), nullable=True)
    best_pattern = Column(String(100), nullable=True)
    worst_pattern = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Numeric(12, 2), nullable=False)
    current_price = Column(Numeric(12, 2), nullable=True)
    unrealized_pnl = Column(Numeric(12, 2), nullable=True)
    stop_loss_price = Column(Numeric(12, 2), nullable=True)
    entry_time = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_code = Column(String(10), nullable=False)
    side = Column(String(4), nullable=False)  # buy / sell
    order_type = Column(String(10), nullable=False)  # market / limit
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=True)
    filled_quantity = Column(Integer, default=0)
    filled_price = Column(Numeric(12, 2), nullable=True)
    status = Column(String(20), default="pending")  # pending / filled / cancelled / failed
    kiwoom_order_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
