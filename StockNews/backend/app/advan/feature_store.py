"""AdvanFeatureDaily 생성 — 일별 시장 피처 계산."""

import logging
from datetime import date, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.advan.models import AdvanFeatureDaily
from app.models.stock_price import StockPrice

logger = logging.getLogger(__name__)


def get_features(db: Session, ticker: str, trade_date: date) -> AdvanFeatureDaily | None:
    """특정 종목/날짜의 피처 조회.

    Args:
        db: DB 세션
        ticker: 종목 코드
        trade_date: 거래일

    Returns:
        AdvanFeatureDaily 또는 None
    """
    return (
        db.query(AdvanFeatureDaily)
        .filter(
            and_(
                AdvanFeatureDaily.ticker == ticker,
                AdvanFeatureDaily.trade_date == trade_date,
            )
        )
        .first()
    )


def _calculate_return(prices: list[StockPrice], days: int) -> float | None:
    """N일 수익률 계산.

    Args:
        prices: 가격 데이터 (최신순 정렬됨)
        days: 기간 (1, 3, 5 등)

    Returns:
        수익률 (%) 또는 None
    """
    if len(prices) < days + 1:
        return None

    current_price = prices[0].close_price
    past_price = prices[days].close_price

    if past_price == 0:
        return None

    return ((current_price - past_price) / past_price) * 100.0


def _calculate_volatility(prices: list[StockPrice], window: int = 20) -> float | None:
    """N일 변동성 계산 (표준편차).

    Args:
        prices: 가격 데이터 (최신순 정렬됨)
        window: 윈도우 크기 (기본 20일)

    Returns:
        변동성 (%) 또는 None
    """
    if len(prices) < window:
        return None

    returns = []
    for i in range(window - 1):
        curr = prices[i].close_price
        prev = prices[i + 1].close_price
        if prev == 0:
            continue
        ret = ((curr - prev) / prev) * 100.0
        returns.append(ret)

    if len(returns) < 2:
        return None

    # 표준편차 계산
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    return variance ** 0.5


def build_features(
    db: Session,
    ticker: str,
    market: str,
    date_from: date,
    date_to: date,
) -> int:
    """종목별 일별 피처 생성.

    Args:
        db: DB 세션
        ticker: 종목 코드
        market: 시장 (KR/US)
        date_from: 시작일
        date_to: 종료일

    Returns:
        생성된 레코드 수
    """
    # 충분한 과거 데이터 확보를 위해 60일 전부터 조회 (20일 volatility 계산용)
    lookback_date = date_from - timedelta(days=60)

    # StockPrice 조회 (최신순)
    all_prices = (
        db.query(StockPrice)
        .filter(
            and_(
                StockPrice.stock_code == ticker,
                StockPrice.date >= lookback_date,
                StockPrice.date <= date_to,
            )
        )
        .order_by(StockPrice.date.desc())
        .all()
    )

    if not all_prices:
        logger.warning(f"No StockPrice data found for ticker={ticker}")
        return 0

    # 날짜별 인덱스 매핑
    price_by_date = {p.date: p for p in all_prices}

    created_count = 0

    # date_from ~ date_to 범위에서 피처 생성
    current_date = date_from
    while current_date <= date_to:
        if current_date not in price_by_date:
            current_date += timedelta(days=1)
            continue

        # 이미 존재하는지 확인
        existing = get_features(db, ticker, current_date)
        if existing:
            current_date += timedelta(days=1)
            continue

        # 해당 날짜부터 과거 방향으로 정렬된 가격 리스트
        prices_from_date = [
            p for p in all_prices
            if p.date <= current_date
        ]
        prices_from_date.sort(key=lambda x: x.date, reverse=True)

        if not prices_from_date:
            current_date += timedelta(days=1)
            continue

        current_price_obj = prices_from_date[0]

        # 수익률 계산
        ret_1d = _calculate_return(prices_from_date, 1)
        ret_3d = _calculate_return(prices_from_date, 3)
        ret_5d = _calculate_return(prices_from_date, 5)

        # 변동성 계산
        volatility_20d = _calculate_volatility(prices_from_date, 20)

        # 달러 거래량 (close_price * volume)
        dollar_volume = current_price_obj.close_price * current_price_obj.volume if current_price_obj.volume else None

        # market_ret, sector_ret, beta는 현재 구현하지 않음 (추후 확장)
        market_ret = None
        sector_ret = None
        beta = None

        # AdvanFeatureDaily 생성
        feature = AdvanFeatureDaily(
            ticker=ticker,
            trade_date=current_date,
            market=market,
            ret_1d=ret_1d,
            ret_3d=ret_3d,
            ret_5d=ret_5d,
            volatility_20d=volatility_20d,
            dollar_volume=dollar_volume,
            beta=beta,
            sector_ret=sector_ret,
            market_ret=market_ret,
            close_price=current_price_obj.close_price,
            volume=current_price_obj.volume,
        )

        db.add(feature)
        created_count += 1

        # 배치 커밋 (100개마다)
        if created_count % 100 == 0:
            db.commit()
            logger.debug(f"Committed {created_count} features for ticker={ticker}")

        current_date += timedelta(days=1)

    # 최종 커밋
    db.commit()

    logger.info(f"Feature building completed for ticker={ticker}: {created_count} records created")
    return created_count
