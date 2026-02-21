# Prediction Verification System Specification

## 1. System Overview

### 목적 (Purpose)
예측 정확도를 검증하기 위해 예측된 주가 방향과 실제 주가 움직임을 비교하는 시스템.

### 설계 원칙
- **ISOLATED 설계**: 기존 코드 수정 없이 새 파일만 추가
- **READ-ONLY**: 기존 테이블(news_event, theme_strength)은 읽기만 수행
- **비동기 검증**: 장 마감 후 자동 실행
- **테마별 집계**: 개별 종목 + 테마 수준 정확도 추적

### Data Flow
```
[Daily Schedule Trigger]
    ↓
[Verification Engine]
    ↓
[Get stocks from news_event] → [Call Prediction Logic] → [Fetch Actual Prices (yfinance)]
    ↓                              ↓                           ↓
    └──────────────────────────────┴───────────────────────────┘
                                   ↓
                    [Compare & Save to daily_prediction_result]
                                   ↓
                    [Aggregate to theme_prediction_accuracy]
                                   ↓
                         [Log to verification_run_log]
                                   ↓
                    [Frontend Dashboard via REST API]
```

---

## 2. Database Schema

### 2.1 daily_prediction_result

일별 개별 종목 예측 검증 결과.

```python
class DailyPredictionResult(Base):
    __tablename__ = "daily_prediction_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str | None] = mapped_column(String(100))
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # "KR" | "US"

    # Prediction data
    predicted_direction: Mapped[str] = mapped_column(String(10), nullable=False)  # "up" | "down" | "neutral"
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    news_count: Mapped[int] = mapped_column(Integer, default=0)

    # Actual data
    previous_close_price: Mapped[float | None] = mapped_column(Float)
    actual_close_price: Mapped[float | None] = mapped_column(Float)
    actual_change_pct: Mapped[float | None] = mapped_column(Float)  # percentage
    actual_direction: Mapped[str | None] = mapped_column(String(10))  # "up" | "down" | "neutral"

    # Verification result
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    error_message: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index('idx_prediction_date_stock', 'prediction_date', 'stock_code'),
        Index('idx_market_date', 'market', 'prediction_date'),
    )
```

### 2.2 theme_prediction_accuracy

테마별 예측 정확도 집계.

```python
class ThemePredictionAccuracy(Base):
    __tablename__ = "theme_prediction_accuracy"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    theme: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)

    # Aggregated metrics
    total_stocks: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1

    # Score metrics
    avg_predicted_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_actual_change_pct: Mapped[float | None] = mapped_column(Float)

    # Theme context
    rise_index_at_prediction: Mapped[float | None] = mapped_column(Float)  # from theme_strength

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_theme_date', 'prediction_date', 'theme'),
    )
```

### 2.3 verification_run_log

검증 실행 로그.

```python
class VerificationRunLog(Base):
    __tablename__ = "verification_run_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # "success" | "partial" | "failed"

    # Metrics
    stocks_verified: Mapped[int] = mapped_column(Integer, default=0)
    stocks_failed: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Error tracking
    error_details: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

---

## 3. API Endpoints

### 3.1 GET /api/v1/verification/daily

일별 검증 결과 조회.

**Query Parameters:**
- `date`: YYYY-MM-DD (required)
- `market`: "KR" | "US" (optional, default: all)
- `limit`: int (optional, default: 50)
- `offset`: int (optional, default: 0)

**Response:**
```json
{
  "date": "2026-02-19",
  "market": "KR",
  "total": 45,
  "correct": 28,
  "accuracy": 0.622,
  "results": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "predicted_direction": "up",
      "predicted_score": 72.5,
      "confidence": 0.85,
      "actual_direction": "up",
      "actual_change_pct": 2.3,
      "is_correct": true,
      "news_count": 15
    }
  ]
}
```

### 3.2 GET /api/v1/verification/accuracy

기간별 정확도 통계.

**Query Parameters:**
- `days`: int (default: 30)
- `market`: "KR" | "US" (optional)

**Response:**
```json
{
  "period_days": 30,
  "market": "KR",
  "overall_accuracy": 0.645,
  "total_predictions": 1350,
  "correct_predictions": 871,
  "by_direction": {
    "up": {"total": 650, "correct": 420, "accuracy": 0.646},
    "down": {"total": 520, "correct": 340, "accuracy": 0.654},
    "neutral": {"total": 180, "correct": 111, "accuracy": 0.617}
  },
  "daily_trend": [
    {"date": "2026-02-19", "accuracy": 0.622, "total": 45},
    {"date": "2026-02-18", "accuracy": 0.680, "total": 42}
  ]
}
```

### 3.3 GET /api/v1/verification/themes

테마별 정확도 (특정일).

**Query Parameters:**
- `date`: YYYY-MM-DD (required)
- `market`: "KR" | "US" (optional)

**Response:**
```json
{
  "date": "2026-02-19",
  "themes": [
    {
      "theme": "반도체",
      "market": "KR",
      "total_stocks": 12,
      "correct_count": 8,
      "accuracy_rate": 0.667,
      "avg_predicted_score": 68.5,
      "avg_actual_change_pct": 1.8,
      "rise_index": 72.3
    }
  ]
}
```

### 3.4 GET /api/v1/verification/themes/trend

테마 정확도 추세.

**Query Parameters:**
- `theme`: string (required)
- `days`: int (default: 30)
- `market`: "KR" | "US" (optional)

**Response:**
```json
{
  "theme": "반도체",
  "period_days": 30,
  "trend": [
    {
      "date": "2026-02-19",
      "accuracy_rate": 0.667,
      "total_stocks": 12,
      "avg_actual_change_pct": 1.8
    }
  ]
}
```

### 3.5 GET /api/v1/verification/stocks/{code}/history

종목별 검증 히스토리.

**Path Parameters:**
- `code`: stock_code

**Query Parameters:**
- `days`: int (default: 30)

**Response:**
```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "period_days": 30,
  "accuracy": 0.733,
  "history": [
    {
      "prediction_date": "2026-02-19",
      "predicted_direction": "up",
      "predicted_score": 72.5,
      "actual_direction": "up",
      "actual_change_pct": 2.3,
      "is_correct": true
    }
  ]
}
```

### 3.6 POST /api/v1/verification/run

수동 검증 실행.

**Query Parameters:**
- `market`: "KR" | "US" (required)
- `date`: YYYY-MM-DD (optional, default: yesterday)

**Response:**
```json
{
  "status": "started",
  "run_id": 123,
  "market": "KR",
  "date": "2026-02-18",
  "message": "Verification job started"
}
```

### 3.7 GET /api/v1/verification/status

검증 시스템 상태.

**Response:**
```json
{
  "status": "healthy",
  "last_run": {
    "KR": {"date": "2026-02-19", "status": "success", "stocks_verified": 45},
    "US": {"date": "2026-02-18", "status": "success", "stocks_verified": 38}
  },
  "next_scheduled": {
    "KR": "2026-02-20T15:35:00+09:00",
    "US": "2026-02-20T16:30:00-05:00"
  }
}
```

---

## 4. Stock Price Fetcher (yfinance)

### 4.1 Ticker Formatting

```python
# backend/app/processing/price_fetcher.py

def format_ticker(stock_code: str, market: str) -> str:
    """
    Format stock code to yfinance ticker.

    KR: append ".KS" suffix (e.g., "005930" → "005930.KS")
    US: use ticker directly (e.g., "AAPL" → "AAPL")
    """
    if market == "KR":
        return f"{stock_code}.KS"
    return stock_code
```

### 4.2 Batch Download

```python
import yfinance as yf
from datetime import datetime, timedelta

async def fetch_prices_batch(
    tickers: list[str],
    start_date: datetime,
    end_date: datetime
) -> dict[str, dict]:
    """
    Batch download stock prices.

    Returns:
        {
            "005930.KS": {
                "previous_close": 70000.0,
                "current_close": 71600.0,
                "change_pct": 2.29
            }
        }
    """
    # yfinance.download is blocking, run in thread pool
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(
        None,
        lambda: yf.download(
            tickers,
            start=start_date,
            end=end_date,
            progress=False,
            threads=True
        )
    )

    results = {}
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                closes = df['Close'].tolist()
            else:
                closes = df['Close'][ticker].dropna().tolist()

            if len(closes) >= 2:
                results[ticker] = {
                    "previous_close": float(closes[-2]),
                    "current_close": float(closes[-1]),
                    "change_pct": ((closes[-1] - closes[-2]) / closes[-2]) * 100
                }
        except (KeyError, IndexError):
            results[ticker] = None

    return results
```

### 4.3 Rate Limiting

```python
import asyncio
from collections import deque

class RateLimiter:
    def __init__(self, requests_per_second: float = 2.0):
        self.rate = requests_per_second
        self.timestamps = deque()

    async def acquire(self):
        now = asyncio.get_event_loop().time()
        while self.timestamps and self.timestamps[0] < now - 1.0:
            self.timestamps.popleft()

        if len(self.timestamps) >= self.rate:
            sleep_time = 1.0 - (now - self.timestamps[0])
            await asyncio.sleep(sleep_time)

        self.timestamps.append(asyncio.get_event_loop().time())
```

### 4.4 Error Handling

```python
async def fetch_with_retry(
    ticker: str,
    max_retries: int = 3,
    backoff: float = 1.0
) -> dict | None:
    """Fetch price with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return await fetch_single_price(ticker)
        except Exception as e:
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(backoff * (2 ** attempt))
```

---

## 5. Verification Engine

### 5.1 Main Verification Flow

```python
# backend/app/processing/verification_engine.py

from datetime import date, timedelta
from sqlalchemy.orm import Session

async def run_verification(
    db: Session,
    target_date: date,
    market: str
) -> VerificationRunLog:
    """
    Main verification workflow.

    Steps:
    1. Get all stocks with news on target_date
    2. Calculate predictions for each stock
    3. Fetch actual prices
    4. Compare and save results
    5. Aggregate theme-level accuracy
    6. Log run
    """
    start_time = datetime.now()
    run_log = VerificationRunLog(
        run_date=target_date,
        market=market,
        status="running"
    )
    db.add(run_log)
    db.commit()

    try:
        # Step 1: Get stocks with news
        stocks = get_stocks_with_news(db, target_date, market)

        # Step 2: Calculate predictions
        predictions = []
        for stock in stocks:
            pred = await calculate_prediction(db, stock, target_date)
            predictions.append(pred)

        # Step 3: Fetch actual prices
        tickers = [format_ticker(p['stock_code'], market) for p in predictions]
        actual_prices = await fetch_prices_batch(
            tickers,
            start_date=target_date - timedelta(days=5),
            end_date=target_date + timedelta(days=1)
        )

        # Step 4: Save daily results
        verified_count = 0
        failed_count = 0

        for pred in predictions:
            ticker = format_ticker(pred['stock_code'], market)
            price_data = actual_prices.get(ticker)

            result = DailyPredictionResult(
                prediction_date=target_date,
                stock_code=pred['stock_code'],
                stock_name=pred['stock_name'],
                market=market,
                predicted_direction=pred['direction'],
                predicted_score=pred['score'],
                confidence=pred['confidence'],
                news_count=pred['news_count']
            )

            if price_data:
                result.previous_close_price = price_data['previous_close']
                result.actual_close_price = price_data['current_close']
                result.actual_change_pct = price_data['change_pct']
                result.actual_direction = get_direction_from_change(price_data['change_pct'])
                result.is_correct = (pred['direction'] == result.actual_direction)
                verified_count += 1
            else:
                result.error_message = "Price data unavailable"
                failed_count += 1

            db.add(result)

        db.commit()

        # Step 5: Aggregate theme accuracy
        await aggregate_theme_accuracy(db, target_date, market)

        # Step 6: Update run log
        duration = (datetime.now() - start_time).total_seconds()
        run_log.status = "success" if failed_count == 0 else "partial"
        run_log.stocks_verified = verified_count
        run_log.stocks_failed = failed_count
        run_log.duration_seconds = duration
        db.commit()

        return run_log

    except Exception as e:
        run_log.status = "failed"
        run_log.error_details = str(e)
        db.commit()
        raise
```

### 5.2 Prediction Calculation

```python
def calculate_prediction(
    db: Session,
    stock: dict,
    target_date: date
) -> dict:
    """
    Calculate prediction using existing prediction logic.

    Reuses logic from backend/app/api/prediction.py
    """
    # Query news up to target_date
    news_items = db.query(NewsEvent).filter(
        NewsEvent.stock_code == stock['stock_code'],
        NewsEvent.market == stock['market'],
        NewsEvent.created_at <= target_date
    ).order_by(NewsEvent.created_at.desc()).limit(100).all()

    if not news_items:
        return {
            'stock_code': stock['stock_code'],
            'stock_name': stock.get('stock_name'),
            'direction': 'neutral',
            'score': 50.0,
            'confidence': 0.0,
            'news_count': 0
        }

    # Calculate scores (same as prediction.py)
    avg_score = sum(n.news_score for n in news_items) / len(news_items)
    avg_sentiment = sum(n.sentiment_score for n in news_items) / len(news_items)

    prediction_score = min(100, max(0, avg_score * 0.6 + (avg_sentiment + 1) * 20))

    # Direction
    if prediction_score > 60:
        direction = "up"
    elif prediction_score < 40:
        direction = "down"
    else:
        direction = "neutral"

    # Confidence
    volume_conf = min(1.0, len(news_items) / 20) * 0.5
    extremity_conf = abs(prediction_score - 50) / 100 * 0.5
    confidence = volume_conf + extremity_conf

    return {
        'stock_code': stock['stock_code'],
        'stock_name': stock.get('stock_name'),
        'direction': direction,
        'score': prediction_score,
        'confidence': confidence,
        'news_count': len(news_items)
    }
```

### 5.3 Direction Mapping

```python
def get_direction_from_change(change_pct: float) -> str:
    """Map price change to direction."""
    if change_pct > 1.0:
        return "up"
    elif change_pct < -1.0:
        return "down"
    else:
        return "neutral"
```

---

## 6. Theme Aggregation

```python
# backend/app/processing/theme_aggregator.py

async def aggregate_theme_accuracy(
    db: Session,
    target_date: date,
    market: str
):
    """
    Aggregate theme-level accuracy from daily results.
    """
    # Get all themes from daily results
    themes_query = db.query(
        NewsEvent.theme
    ).filter(
        NewsEvent.market == market,
        NewsEvent.created_at <= target_date,
        NewsEvent.theme.isnot(None)
    ).distinct()

    themes = [t[0] for t in themes_query.all()]

    for theme in themes:
        # Get stocks with this theme
        stocks_with_theme = db.query(NewsEvent.stock_code).filter(
            NewsEvent.theme == theme,
            NewsEvent.market == market,
            NewsEvent.created_at <= target_date
        ).distinct().all()

        stock_codes = [s[0] for s in stocks_with_theme]

        # Get verification results for these stocks
        results = db.query(DailyPredictionResult).filter(
            DailyPredictionResult.prediction_date == target_date,
            DailyPredictionResult.stock_code.in_(stock_codes),
            DailyPredictionResult.market == market
        ).all()

        if not results:
            continue

        total_stocks = len(results)
        correct_count = sum(1 for r in results if r.is_correct)
        accuracy_rate = correct_count / total_stocks if total_stocks > 0 else 0.0

        avg_predicted_score = sum(r.predicted_score for r in results) / total_stocks

        actual_changes = [r.actual_change_pct for r in results if r.actual_change_pct is not None]
        avg_actual_change = sum(actual_changes) / len(actual_changes) if actual_changes else None

        # Get rise_index from theme_strength
        theme_strength = db.query(ThemeStrength).filter(
            ThemeStrength.theme == theme,
            ThemeStrength.created_at <= target_date
        ).order_by(ThemeStrength.created_at.desc()).first()

        rise_index = theme_strength.rise_index if theme_strength else None

        # Save theme accuracy
        theme_accuracy = ThemePredictionAccuracy(
            prediction_date=target_date,
            theme=theme,
            market=market,
            total_stocks=total_stocks,
            correct_count=correct_count,
            accuracy_rate=accuracy_rate,
            avg_predicted_score=avg_predicted_score,
            avg_actual_change_pct=avg_actual_change,
            rise_index_at_prediction=rise_index
        )

        db.add(theme_accuracy)

    db.commit()
```

---

## 7. Scheduler Design

### 7.1 Scheduler Configuration

```python
# backend/app/collectors/verification_scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

scheduler = BackgroundScheduler()

def schedule_verification_jobs():
    """Schedule verification jobs for KR and US markets."""

    # KR market: Run at 15:35 KST (after 15:30 close)
    scheduler.add_job(
        func=run_kr_verification_sync,
        trigger=CronTrigger(
            day_of_week='mon-fri',
            hour=15,
            minute=35,
            timezone='Asia/Seoul'
        ),
        id='kr_verification',
        name='KR Market Verification',
        replace_existing=True
    )

    # US market: Run at 16:30 EST (after 16:00 close)
    scheduler.add_job(
        func=run_us_verification_sync,
        trigger=CronTrigger(
            day_of_week='mon-fri',
            hour=16,
            minute=30,
            timezone='America/New_York'
        ),
        id='us_verification',
        name='US Market Verification',
        replace_existing=True
    )

    scheduler.start()

def run_kr_verification_sync():
    """Sync wrapper for KR verification."""
    asyncio.run(_run_verification_with_retry("KR"))

def run_us_verification_sync():
    """Sync wrapper for US verification."""
    asyncio.run(_run_verification_with_retry("US"))

async def _run_verification_with_retry(
    market: str,
    max_retries: int = 3,
    retry_delay: int = 300  # 5 minutes
):
    """Run verification with retry on failure."""
    from datetime import date, timedelta
    from app.core.database import SessionLocal

    target_date = date.today() - timedelta(days=1)  # Verify previous day

    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            await run_verification(db, target_date, market)
            db.close()
            return
        except Exception as e:
            if attempt == max_retries - 1:
                # Log final failure
                db = SessionLocal()
                log = VerificationRunLog(
                    run_date=target_date,
                    market=market,
                    status="failed",
                    error_details=f"Failed after {max_retries} retries: {str(e)}"
                )
                db.add(log)
                db.commit()
                db.close()
                raise

            await asyncio.sleep(retry_delay)
```

### 7.2 Integration with Main App

```python
# backend/app/main.py

from app.collectors.verification_scheduler import schedule_verification_jobs

@app.on_event("startup")
def startup_event():
    """Start schedulers on app startup."""
    # ... existing schedulers ...
    schedule_verification_jobs()
```

---

## 8. Frontend Components

### 8.1 Page Structure

```typescript
// frontend/src/pages/VerificationPage.tsx

import React, { useState } from 'react';
import { AccuracyOverviewCard } from '@/components/verification/AccuracyOverviewCard';
import { DailyAccuracyChart } from '@/components/verification/DailyAccuracyChart';
import { StockResultsTable } from '@/components/verification/StockResultsTable';
import { ThemeAccuracyBreakdown } from '@/components/verification/ThemeAccuracyBreakdown';
import { useVerification } from '@/hooks/useVerification';
import { useMarketContext } from '@/contexts/MarketContext';

export const VerificationPage: React.FC = () => {
  const { selectedMarket } = useMarketContext();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [days, setDays] = useState(30);

  const { accuracy, dailyResults, themeAccuracy, isLoading } = useVerification({
    market: selectedMarket,
    date: selectedDate,
    days
  });

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">예측 검증</h1>
        <div className="flex gap-4">
          <input
            type="date"
            value={selectedDate.toISOString().split('T')[0]}
            onChange={(e) => setSelectedDate(new Date(e.target.value))}
            className="px-4 py-2 border rounded-lg"
          />
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg"
          >
            <option value={7}>7일</option>
            <option value={30}>30일</option>
            <option value={90}>90일</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">Loading...</div>
      ) : (
        <>
          <AccuracyOverviewCard accuracy={accuracy} />
          <DailyAccuracyChart data={accuracy?.daily_trend || []} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <StockResultsTable results={dailyResults?.results || []} />
            <ThemeAccuracyBreakdown themes={themeAccuracy?.themes || []} />
          </div>
        </>
      )}
    </div>
  );
};
```

### 8.2 Sidebar Navigation Update

```typescript
// frontend/src/components/layout/Sidebar.tsx

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/news', label: 'Latest News', icon: '📰' },
  { path: '/themes', label: 'Theme Analysis', icon: '🎯' },
  { path: '/verification', label: '예측 검증', icon: '✅' },  // NEW
];
```

### 8.3 Route Configuration

```typescript
// frontend/src/App.tsx

import { VerificationPage } from './pages/VerificationPage';

<Route path="/verification" element={<VerificationPage />} />
```

---

## 9. Error Handling

### 9.1 Market Holidays

```python
import pandas_market_calendars as mcal

def is_market_open(date: date, market: str) -> bool:
    """Check if market was open on given date."""
    if market == "KR":
        calendar = mcal.get_calendar("XKRX")  # Korea Exchange
    else:
        calendar = mcal.get_calendar("NYSE")

    schedule = calendar.schedule(start_date=date, end_date=date)
    return not schedule.empty
```

### 9.2 Missing Stock Data

```python
# In verification_engine.py

if not price_data:
    if not is_market_open(target_date, market):
        error_message = "Market closed (holiday)"
    else:
        error_message = "Stock delisted or data unavailable"

    result.error_message = error_message
    result.is_correct = None
```

### 9.3 API Timeout Handling

```python
import asyncio

async def fetch_with_timeout(
    coro,
    timeout: float = 30.0
) -> any:
    """Execute coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return None
```

### 9.4 No Predictions Case

```python
# In get_stocks_with_news()

def get_stocks_with_news(
    db: Session,
    target_date: date,
    market: str,
    min_news_count: int = 5  # Skip stocks with too few news
) -> list[dict]:
    """Get stocks that have sufficient news for prediction."""
    stocks = db.query(
        NewsEvent.stock_code,
        NewsEvent.stock_name,
        func.count(NewsEvent.id).label('news_count')
    ).filter(
        NewsEvent.market == market,
        NewsEvent.created_at <= target_date,
        NewsEvent.created_at >= target_date - timedelta(days=30)
    ).group_by(
        NewsEvent.stock_code,
        NewsEvent.stock_name
    ).having(
        func.count(NewsEvent.id) >= min_news_count
    ).all()

    return [
        {
            'stock_code': s.stock_code,
            'stock_name': s.stock_name,
            'market': market
        }
        for s in stocks
    ]
```

---

## 10. Complete File Structure

### Backend Files

```
backend/
├── app/
│   ├── models/
│   │   └── verification.py                    # NEW: 3 SQLAlchemy models
│   ├── schemas/
│   │   └── verification.py                    # NEW: Pydantic schemas
│   ├── api/
│   │   ├── verification.py                    # NEW: 7 API endpoints
│   │   └── router.py                          # MODIFY: include verification router
│   ├── processing/
│   │   ├── price_fetcher.py                   # NEW: yfinance integration
│   │   ├── verification_engine.py             # NEW: main verification logic
│   │   └── theme_aggregator.py                # NEW: theme accuracy aggregation
│   ├── collectors/
│   │   └── verification_scheduler.py          # NEW: APScheduler jobs
│   └── core/
│       ├── database.py                        # MODIFY: import new models
│       └── config.py                          # (no changes)
└── tests/
    ├── unit/
    │   ├── test_price_fetcher.py              # NEW: price fetcher tests
    │   ├── test_verification_engine.py        # NEW: engine logic tests
    │   ├── test_theme_aggregator.py           # NEW: aggregation tests
    │   └── test_verification_api.py           # NEW: API endpoint tests
    └── integration/
        └── test_verification_flow.py          # NEW: end-to-end verification
```

### Frontend Files

```
frontend/
├── src/
│   ├── pages/
│   │   └── VerificationPage.tsx               # NEW: main verification page
│   ├── components/
│   │   ├── layout/
│   │   │   └── Sidebar.tsx                    # MODIFY: add verification nav item
│   │   └── verification/
│   │       ├── AccuracyOverviewCard.tsx       # NEW: accuracy summary card
│   │       ├── DailyAccuracyChart.tsx         # NEW: Recharts line chart
│   │       ├── StockResultsTable.tsx          # NEW: sortable results table
│   │       └── ThemeAccuracyBreakdown.tsx     # NEW: theme accuracy bar chart
│   ├── hooks/
│   │   └── useVerification.ts                 # NEW: TanStack Query hooks
│   ├── api/
│   │   └── verification.ts                    # NEW: API client functions
│   ├── types/
│   │   └── verification.ts                    # NEW: TypeScript types
│   └── App.tsx                                # MODIFY: add /verification route
└── tests/
    └── components/
        └── verification/
            ├── AccuracyOverviewCard.test.tsx  # NEW
            ├── DailyAccuracyChart.test.tsx    # NEW
            ├── StockResultsTable.test.tsx     # NEW
            └── ThemeAccuracyBreakdown.test.tsx # NEW
```

### Alembic Migration

```
backend/alembic/versions/
└── xxxx_add_verification_tables.py            # NEW: migration script
```

---

## 11. Alembic Migration SQL

```python
"""add verification tables

Revision ID: xxxx
Revises: yyyy
Create Date: 2026-02-19
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create daily_prediction_result
    op.create_table(
        'daily_prediction_result',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('stock_code', sa.String(20), nullable=False),
        sa.Column('stock_name', sa.String(100), nullable=True),
        sa.Column('market', sa.String(5), nullable=False),
        sa.Column('predicted_direction', sa.String(10), nullable=False),
        sa.Column('predicted_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('news_count', sa.Integer(), server_default='0'),
        sa.Column('previous_close_price', sa.Float(), nullable=True),
        sa.Column('actual_close_price', sa.Float(), nullable=True),
        sa.Column('actual_change_pct', sa.Float(), nullable=True),
        sa.Column('actual_direction', sa.String(10), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prediction_date_stock', 'daily_prediction_result',
                    ['prediction_date', 'stock_code'])
    op.create_index('idx_market_date', 'daily_prediction_result',
                    ['market', 'prediction_date'])
    op.create_index('idx_dpr_prediction_date', 'daily_prediction_result',
                    ['prediction_date'])
    op.create_index('idx_dpr_stock_code', 'daily_prediction_result',
                    ['stock_code'])
    op.create_index('idx_dpr_market', 'daily_prediction_result',
                    ['market'])

    # Create theme_prediction_accuracy
    op.create_table(
        'theme_prediction_accuracy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('theme', sa.String(50), nullable=False),
        sa.Column('market', sa.String(5), nullable=False),
        sa.Column('total_stocks', sa.Integer(), server_default='0'),
        sa.Column('correct_count', sa.Integer(), server_default='0'),
        sa.Column('accuracy_rate', sa.Float(), server_default='0.0'),
        sa.Column('avg_predicted_score', sa.Float(), server_default='0.0'),
        sa.Column('avg_actual_change_pct', sa.Float(), nullable=True),
        sa.Column('rise_index_at_prediction', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_theme_date', 'theme_prediction_accuracy',
                    ['prediction_date', 'theme'])
    op.create_index('idx_tpa_prediction_date', 'theme_prediction_accuracy',
                    ['prediction_date'])
    op.create_index('idx_tpa_theme', 'theme_prediction_accuracy',
                    ['theme'])
    op.create_index('idx_tpa_market', 'theme_prediction_accuracy',
                    ['market'])

    # Create verification_run_log
    op.create_table(
        'verification_run_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_date', sa.Date(), nullable=False),
        sa.Column('market', sa.String(5), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('stocks_verified', sa.Integer(), server_default='0'),
        sa.Column('stocks_failed', sa.Integer(), server_default='0'),
        sa.Column('duration_seconds', sa.Float(), server_default='0.0'),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_vrl_run_date', 'verification_run_log', ['run_date'])

def downgrade():
    op.drop_table('verification_run_log')
    op.drop_table('theme_prediction_accuracy')
    op.drop_table('daily_prediction_result')
```

---

## 12. TypeScript Types

```typescript
// frontend/src/types/verification.ts

export interface DailyPredictionResult {
  stock_code: string;
  stock_name: string;
  predicted_direction: 'up' | 'down' | 'neutral';
  predicted_score: number;
  confidence: number;
  actual_direction?: 'up' | 'down' | 'neutral';
  actual_change_pct?: number;
  is_correct?: boolean;
  news_count: number;
  error_message?: string;
}

export interface DailyVerificationResponse {
  date: string;
  market: string;
  total: number;
  correct: number;
  accuracy: number;
  results: DailyPredictionResult[];
}

export interface DirectionStats {
  total: number;
  correct: number;
  accuracy: number;
}

export interface DailyTrend {
  date: string;
  accuracy: number;
  total: number;
}

export interface AccuracyResponse {
  period_days: number;
  market: string;
  overall_accuracy: number;
  total_predictions: number;
  correct_predictions: number;
  by_direction: {
    up: DirectionStats;
    down: DirectionStats;
    neutral: DirectionStats;
  };
  daily_trend: DailyTrend[];
}

export interface ThemeAccuracy {
  theme: string;
  market: string;
  total_stocks: number;
  correct_count: number;
  accuracy_rate: number;
  avg_predicted_score: number;
  avg_actual_change_pct?: number;
  rise_index?: number;
}

export interface ThemeAccuracyResponse {
  date: string;
  themes: ThemeAccuracy[];
}

export interface ThemeTrendPoint {
  date: string;
  accuracy_rate: number;
  total_stocks: number;
  avg_actual_change_pct?: number;
}

export interface ThemeTrendResponse {
  theme: string;
  period_days: number;
  trend: ThemeTrendPoint[];
}

export interface StockHistoryPoint {
  prediction_date: string;
  predicted_direction: 'up' | 'down' | 'neutral';
  predicted_score: number;
  actual_direction?: 'up' | 'down' | 'neutral';
  actual_change_pct?: number;
  is_correct?: boolean;
}

export interface StockHistoryResponse {
  stock_code: string;
  stock_name: string;
  period_days: number;
  accuracy: number;
  history: StockHistoryPoint[];
}

export interface VerificationRunResponse {
  status: string;
  run_id: number;
  market: string;
  date: string;
  message: string;
}

export interface MarketStatus {
  date: string;
  status: string;
  stocks_verified: number;
}

export interface VerificationStatusResponse {
  status: string;
  last_run: {
    KR?: MarketStatus;
    US?: MarketStatus;
  };
  next_scheduled: {
    KR?: string;
    US?: string;
  };
}
```

---

## 13. Dependencies

### Backend

```toml
# backend/pyproject.toml

[project]
dependencies = [
    # ... existing ...
    "yfinance>=0.2.36",
    "pandas-market-calendars>=4.3.0",
]
```

### Frontend

```json
// frontend/package.json (no new dependencies)
```

---

## 14. Implementation Checklist

### Phase 1: Backend Core (Day 1-2)
- [ ] Create database models (verification.py)
- [ ] Create Pydantic schemas
- [ ] Implement price_fetcher.py with yfinance
- [ ] Implement verification_engine.py core logic
- [ ] Implement theme_aggregator.py
- [ ] Write unit tests for all processing modules

### Phase 2: Backend API (Day 3)
- [ ] Implement 7 API endpoints in verification.py
- [ ] Add verification router to main router
- [ ] Write API endpoint tests
- [ ] Write integration test for full flow

### Phase 3: Scheduler (Day 4)
- [ ] Implement verification_scheduler.py
- [ ] Integrate with main app startup
- [ ] Test scheduled jobs (use test triggers)

### Phase 4: Migration (Day 4)
- [ ] Create Alembic migration
- [ ] Test migration up/down
- [ ] Verify indexes created

### Phase 5: Frontend (Day 5-6)
- [ ] Create TypeScript types
- [ ] Implement API client (verification.ts)
- [ ] Implement useVerification hook
- [ ] Create VerificationPage
- [ ] Create 4 visualization components
- [ ] Update Sidebar navigation
- [ ] Write component tests

### Phase 6: Testing & Refinement (Day 7)
- [ ] End-to-end testing with real yfinance data
- [ ] Load testing for batch price fetching
- [ ] Error scenario testing (holidays, delisted stocks)
- [ ] Documentation update

---

## 15. Performance Considerations

### 15.1 Batch Processing
- Use `yfinance.download()` with multiple tickers (up to 50 at once)
- Parallel processing with asyncio for independent tasks
- Cache price data in Redis for 24 hours

### 15.2 Database Optimization
- Indexes on (prediction_date, stock_code), (market, prediction_date)
- Partition daily_prediction_result by month (future optimization)
- Archive old results after 1 year

### 15.3 Rate Limiting
- 2 requests/second to yfinance
- Exponential backoff on failures
- Circuit breaker pattern for repeated failures

---

## 16. Monitoring & Alerts

### 16.1 Key Metrics
- Verification success rate (target: >95%)
- Average verification duration (target: <5 minutes)
- Price fetch failure rate (target: <5%)
- Overall prediction accuracy trend

### 16.2 Alert Conditions
- Verification job failed 3 times consecutively
- Accuracy drops below 40% for 7 consecutive days
- Price fetch failure rate >20%
- Verification duration >15 minutes

---

## 17. Future Enhancements

### 17.1 Advanced Analytics
- Confusion matrix visualization (predicted vs actual)
- Confidence calibration analysis
- Feature importance (which news factors correlate with accuracy)

### 17.2 Multi-Day Predictions
- 3-day, 5-day, 10-day forecast verification
- Cumulative return tracking

### 17.3 Strategy Backtesting
- Simulate trading based on predictions
- P&L tracking
- Risk-adjusted returns (Sharpe ratio)

### 17.4 Real-time Price Streaming
- Replace yfinance with WebSocket price feeds (Finnhub, Yahoo)
- Intraday verification (not just daily close)

---

**END OF SPECIFICATION**
