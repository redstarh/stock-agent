# Prediction Verification System — Architecture Analysis

## 문서 개요

**대상 시스템:** StockNews Prediction Verification System
**작성일:** 2026-02-19
**목적:** 예측 검증 시스템의 설계 검증, 기존 시스템 통합 분석, 리스크 평가

이 문서는 [PredictionVerification-Spec.md](./PredictionVerification-Spec.md) 명세를 기반으로 실제 구현 시 고려해야 할 아키텍처 관점의 분석을 제공합니다.

---

## 1. Integration Points Analysis

### 1.1 READ-ONLY from Existing Tables

검증 시스템은 기존 테이블을 **읽기만** 수행합니다. 이는 coupling을 최소화하는 ISOLATED 설계 원칙입니다.

#### news_event 테이블 (READ-ONLY)

```python
# backend/app/processing/verification_engine.py

from app.models.news_event import NewsEvent

def get_stocks_with_news(
    db: Session,
    target_date: date,
    market: str,
    min_news_count: int = 5
) -> list[dict]:
    """
    검증 대상 종목 조회 (뉴스가 충분한 종목만).

    READ-ONLY: news_event 테이블에서 종목 목록 추출.
    """
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

#### prediction.py 로직 재사용 (READ-ONLY)

```python
# backend/app/processing/verification_engine.py

def calculate_prediction(
    db: Session,
    stock: dict,
    target_date: date
) -> dict:
    """
    예측 점수 계산 (기존 prediction.py 로직 재사용).

    READ-ONLY: news_event 테이블에서 뉴스 조회 후 점수 계산.
    """
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

    # 기존 prediction.py와 동일한 로직
    avg_score = sum(n.news_score for n in news_items) / len(news_items)
    avg_sentiment = sum(n.sentiment_score for n in news_items) / len(news_items)
    prediction_score = min(100, max(0, avg_score * 0.6 + (avg_sentiment + 1) * 20))

    if prediction_score > 60:
        direction = "up"
    elif prediction_score < 40:
        direction = "down"
    else:
        direction = "neutral"

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

### 1.2 New DB Tables (ISOLATED)

3개의 새 테이블 생성, 기존 Base/engine 재사용:

```python
# backend/app/models/verification.py (NEW FILE)

from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DailyPredictionResult(Base):
    """일별 개별 종목 예측 검증 결과."""

    __tablename__ = "daily_prediction_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)

    # Prediction data
    predicted_direction: Mapped[str] = mapped_column(String(10), nullable=False)
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    news_count: Mapped[int] = mapped_column(Integer, default=0)

    # Actual data
    previous_close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_direction: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Verification result
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index('idx_prediction_date_stock', 'prediction_date', 'stock_code'),
        Index('idx_market_date', 'market', 'prediction_date'),
    )


class ThemePredictionAccuracy(Base):
    """테마별 예측 정확도 집계."""

    __tablename__ = "theme_prediction_accuracy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    theme: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)

    # Aggregated metrics
    total_stocks: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Score metrics
    avg_predicted_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_actual_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Theme context
    rise_index_at_prediction: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_theme_date', 'prediction_date', 'theme'),
    )


class VerificationRunLog(Base):
    """검증 실행 로그."""

    __tablename__ = "verification_run_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Metrics
    stocks_verified: Mapped[int] = mapped_column(Integer, default=0)
    stocks_failed: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Error tracking
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Integration:** `app/core/database.py`는 수정 불필요 (Base.metadata가 자동으로 새 모델 포함).

### 1.3 New API Routes

```python
# backend/app/api/verification.py (NEW FILE)

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from app.core.limiter import limiter

from app.core.database import get_db
from app.models.verification import DailyPredictionResult, ThemePredictionAccuracy
from app.schemas.verification import (
    DailyVerificationResponse,
    AccuracyResponse,
    ThemeAccuracyResponse,
)

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])


@router.get("/daily", response_model=DailyVerificationResponse)
@limiter.limit("60/minute")
async def get_daily_verification(
    request: Request,
    response: Response,
    date: str = Query(..., description="YYYY-MM-DD"),
    market: str | None = Query(None, description="KR or US"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """일별 검증 결과 조회."""
    # Implementation here
    pass


@router.get("/accuracy", response_model=AccuracyResponse)
@limiter.limit("60/minute")
async def get_accuracy_stats(
    request: Request,
    response: Response,
    days: int = Query(30, ge=1, le=365),
    market: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """기간별 정확도 통계."""
    # Implementation here
    pass


# ... 5 more endpoints (total 7)
```

**Router Registration:**

```python
# backend/app/api/router.py (MODIFY)

from app.api.verification import router as verification_router

api_v1_router.include_router(verification_router)  # ADD THIS LINE
```

### 1.4 New Scheduler Jobs

```python
# backend/app/collectors/verification_scheduler.py (NEW FILE)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def schedule_verification_jobs():
    """검증 스케줄러 초기화 (KR/US 별도 job)."""

    # KR market: 15:35 KST (장 마감 15:30 후 5분)
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
        replace_existing=True,
        max_instances=1,
    )

    # US market: 16:30 EST (장 마감 16:00 후 30분)
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
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info("Verification scheduler started (KR 15:35 KST, US 16:30 EST)")


def run_kr_verification_sync():
    """KR 검증 동기 래퍼."""
    asyncio.run(_run_verification_with_retry("KR"))


def run_us_verification_sync():
    """US 검증 동기 래퍼."""
    asyncio.run(_run_verification_with_retry("US"))


async def _run_verification_with_retry(
    market: str,
    max_retries: int = 3,
    retry_delay: int = 300  # 5분
):
    """검증 실행 (retry 로직 포함)."""
    from datetime import date, timedelta
    from app.core.database import SessionLocal
    from app.processing.verification_engine import run_verification

    target_date = date.today() - timedelta(days=1)  # 전날 데이터 검증

    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            await run_verification(db, target_date, market)
            db.close()
            logger.info(f"{market} verification completed for {target_date}")
            return
        except Exception as e:
            logger.error(f"{market} verification attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                # Final failure: log to DB
                db = SessionLocal()
                from app.models.verification import VerificationRunLog
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

**Main App Integration:**

```python
# backend/app/main.py (MODIFY)

@asynccontextmanager
async def lifespan(application: FastAPI):
    """애플리케이션 시작/종료 이벤트."""
    Base.metadata.create_all(bind=engine)

    # Existing scheduler
    from app.collectors.scheduler import create_scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("News collection scheduler started")

    # NEW: Verification scheduler
    from app.collectors.verification_scheduler import schedule_verification_jobs
    schedule_verification_jobs()
    logger.info("Verification scheduler started")

    yield

    # Shutdown logic (existing)
```

### 1.5 Frontend Integration

#### Route Registration

```typescript
// frontend/src/App.tsx (MODIFY)

import VerificationPage from './pages/VerificationPage';

<Routes>
  <Route path="/" element={<DashboardPage />} />
  <Route path="/news" element={<NewsPage />} />
  <Route path="/stocks/:code" element={<StockDetailPage />} />
  <Route path="/themes" element={<ThemeAnalysisPage />} />
  <Route path="/verification" element={<VerificationPage />} /> {/* ADD */}
</Routes>
```

#### Sidebar Navigation

```typescript
// frontend/src/components/layout/Sidebar.tsx (MODIFY)

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/news', label: 'Latest News', icon: '📰' },
  { path: '/themes', label: 'Theme Analysis', icon: '🎯' },
  { path: '/verification', label: '예측 검증', icon: '✅' },  // ADD THIS LINE
];
```

---

## 2. Stock Price API Comparison

### 2.1 yfinance (권장)

**장점:**
- ✅ 이미 dependency에 포함 (`pyproject.toml`에 명시 가능)
- ✅ KR + US 모두 지원 (`.KS` suffix for Korean stocks)
- ✅ 무료, rate limit 느슨 (개인 사용 기준)
- ✅ Batch download 지원 (`yf.download(tickers_list)`)

**단점:**
- ⚠️ Unofficial API (Yahoo Finance 스크래핑)
- ⚠️ 가끔 데이터 누락 (휴장일, 상장폐지 등)

**사용 예시:**

```python
import yfinance as yf
from datetime import datetime, timedelta

# Single stock
ticker = yf.Ticker("005930.KS")  # 삼성전자
hist = ticker.history(period="5d")

# Batch download (추천)
tickers = ["005930.KS", "000660.KS", "AAPL", "MSFT"]
df = yf.download(tickers, start="2024-01-01", end="2024-01-05", progress=False, threads=True)
```

### 2.2 pykrx (한국 전용)

**장점:**
- ✅ 공식 KRX 데이터
- ✅ 정확도 높음
- ✅ 무료

**단점:**
- ❌ KR 전용 (US 지원 안 됨)
- ❌ Batch download 미지원 (loop 필요)
- ❌ 새 dependency 추가 필요

### 2.3 Alpha Vantage

**장점:**
- ✅ 공식 API
- ✅ KR + US 지원

**단점:**
- ❌ Free tier: 25 requests/day (너무 적음)
- ❌ API key 관리 필요

### 2.4 권장 사항

**✅ yfinance 사용 (1순위)**

이유:
1. 이미 프로젝트에 포함 가능 (추가 의존성 최소)
2. KR/US 통합 처리
3. Batch download로 rate limit 회피
4. MVP에 충분한 정확도

**Fallback 전략:** pykrx를 secondary로 고려 (yfinance 실패 시).

---

## 3. Risk Analysis

### 3.1 Coupling Risk (낮음)

**리스크:** 검증 시스템이 기존 시스템에 영향을 줄 가능성.

**완화 방안:**
- ✅ READ-ONLY 설계: `news_event` 테이블 읽기만 수행
- ✅ Isolated DB tables: 새 테이블 3개만 추가, 기존 테이블 수정 없음
- ✅ Feature flag 지원 (`settings.enable_verification`)

```python
# app/core/config.py (MODIFY)

class Settings(BaseSettings):
    # Existing settings...

    # NEW: Verification feature flag
    enable_verification: bool = True
```

### 3.2 DB Migration Risk (중간)

**리스크:** 새 테이블 추가 시 migration 실패.

**완화 방안:**
- ✅ MVP: `Base.metadata.create_all()` (자동 생성)
- ✅ Production: Alembic migration 스크립트 제공 (downgrade 지원)

```python
# alembic/versions/xxxx_add_verification_tables.py

def upgrade():
    # Create 3 tables with indexes
    pass

def downgrade():
    # Drop tables (rollback)
    op.drop_table('verification_run_log')
    op.drop_table('theme_prediction_accuracy')
    op.drop_table('daily_prediction_result')
```

### 3.3 Rate Limit Risk (높음)

**리스크:** yfinance API를 과도하게 호출하여 차단.

**완화 방안:**
- ✅ Batch download (50 tickers at once)
- ✅ Rate limiter 구현 (2 req/sec)
- ✅ Exponential backoff retry
- ✅ Redis cache (24시간)

```python
# backend/app/collectors/price_fetcher.py (NEW FILE)

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

### 3.4 Market Holiday Risk (중간)

**리스크:** 휴장일에 검증 실행 시 데이터 없음.

**완화 방안:**
- ✅ Market calendar 체크 (`pandas-market-calendars`)
- ✅ Graceful handling: 휴장일은 skip하고 log 남김

```python
import pandas_market_calendars as mcal

def is_market_open(date: date, market: str) -> bool:
    """시장 개장일인지 확인."""
    if market == "KR":
        calendar = mcal.get_calendar("XKRX")  # Korea Exchange
    else:
        calendar = mcal.get_calendar("NYSE")

    schedule = calendar.schedule(start_date=date, end_date=date)
    return not schedule.empty
```

### 3.5 Data Freshness Risk (낮음)

**리스크:** 예측 시점과 검증 시점 사이 데이터 변경.

**완화 방안:**
- ✅ `prediction_date` 기준으로 뉴스 조회 (`created_at <= prediction_date`)
- ✅ Time-travel query: 과거 시점 데이터만 사용

---

## 4. Code Style Patterns

### 4.1 SQLAlchemy Model (Mapped[] + mapped_column)

프로젝트 표준 패턴:

```python
from sqlalchemy import Integer, String, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class DailyPredictionResult(Base):
    __tablename__ = "daily_prediction_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    __table_args__ = (
        Index('idx_stock_date', 'stock_code', 'prediction_date'),
    )
```

### 4.2 Pydantic Schema (BaseModel + field_validator)

```python
from pydantic import BaseModel, field_validator

class DailyVerificationResponse(BaseModel):
    """일별 검증 결과 응답."""

    date: str
    market: str
    total: int
    correct: int
    accuracy: float
    results: list[DailyPredictionResult]

    @field_validator("accuracy")
    @classmethod
    def validate_accuracy(cls, v):
        if not 0 <= v <= 1.0:
            raise ValueError("accuracy must be between 0 and 1")
        return v
```

### 4.3 FastAPI Endpoint (@limiter.limit + Depends(get_db))

```python
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from app.core.limiter import limiter
from app.core.database import get_db

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])

@router.get("/daily")
@limiter.limit("60/minute")
async def get_daily_verification(
    request: Request,
    response: Response,
    date: str,
    db: Session = Depends(get_db)
):
    """일별 검증 결과."""
    # Implementation
    pass
```

### 4.4 APScheduler (BackgroundScheduler + CronTrigger)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

scheduler.add_job(
    func=job_function,
    trigger=CronTrigger(day_of_week='mon-fri', hour=15, minute=35, timezone='Asia/Seoul'),
    id='job_id',
    replace_existing=True,
    max_instances=1,
)

scheduler.start()
```

### 4.5 React Page (useMarket + useQuery + Loading)

```typescript
import { useMarket } from '../contexts/MarketContext';
import { useQuery } from '@tanstack/react-query';
import Loading from '../components/common/Loading';

export default function VerificationPage() {
  const { market } = useMarket();

  const { data, isLoading, error } = useQuery({
    queryKey: ['verification', 'summary', market],
    queryFn: () => fetchVerificationSummary(market),
  });

  if (isLoading) return <Loading message="로딩 중..." />;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div className="space-y-6">
      {/* Content */}
    </div>
  );
}
```

### 4.6 TanStack Query Hook

```typescript
// frontend/src/hooks/useVerification.ts (NEW FILE)

import { useQuery } from '@tanstack/react-query';
import { fetchDailyVerification, fetchAccuracyStats } from '../api/verification';

export function useDailyVerification(date: string, market: string) {
  return useQuery({
    queryKey: ['verification', 'daily', date, market],
    queryFn: () => fetchDailyVerification(date, market),
    staleTime: 60_000, // 1분
  });
}

export function useAccuracyStats(days: number, market: string) {
  return useQuery({
    queryKey: ['verification', 'accuracy', days, market],
    queryFn: () => fetchAccuracyStats(days, market),
    staleTime: 300_000, // 5분
  });
}
```

---

## 5. Rollback Strategy

### 5.1 Feature Flag

```python
# app/core/config.py

class Settings(BaseSettings):
    enable_verification: bool = True  # Set to False to disable
```

**Conditional startup:**

```python
# app/main.py

@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)

    # Existing scheduler
    scheduler = create_scheduler()
    scheduler.start()

    # Verification (conditional)
    if settings.enable_verification:
        schedule_verification_jobs()
        logger.info("Verification scheduler started")
    else:
        logger.info("Verification scheduler disabled (feature flag)")

    yield
```

### 5.2 Clean Removal Steps

1. **Disable feature flag:**
   ```bash
   export ENABLE_VERIFICATION=false
   # Or in .env: ENABLE_VERIFICATION=false
   ```

2. **Remove frontend route:**
   ```typescript
   // frontend/src/App.tsx
   // Comment out or remove:
   // <Route path="/verification" element={<VerificationPage />} />
   ```

3. **Remove sidebar nav:**
   ```typescript
   // frontend/src/components/layout/Sidebar.tsx
   // Remove verification nav item
   ```

4. **Drop DB tables (Alembic):**
   ```bash
   cd backend
   alembic downgrade -1  # Rollback to previous migration
   ```

5. **Remove files:**
   ```bash
   rm backend/app/models/verification.py
   rm backend/app/schemas/verification.py
   rm backend/app/api/verification.py
   rm backend/app/processing/verification_engine.py
   rm backend/app/processing/price_fetcher.py
   rm backend/app/collectors/verification_scheduler.py
   rm frontend/src/pages/VerificationPage.tsx
   rm -r frontend/src/components/verification/
   ```

**Impact:** Zero impact on existing features (news collection, prediction API, theme analysis).

---

## 6. Security

### 6.1 Rate Limiting

모든 API endpoint에 적용:

```python
@router.get("/daily")
@limiter.limit("60/minute")
async def get_daily_verification(request: Request, response: Response, ...):
    pass
```

### 6.2 SQL Injection Protection

SQLAlchemy ORM 사용으로 자동 방어:

```python
# Safe: Parameterized query
db.query(DailyPredictionResult).filter(
    DailyPredictionResult.stock_code == stock_code
).all()

# Unsafe (avoided): Raw SQL
# db.execute(f"SELECT * FROM daily_prediction_result WHERE stock_code = '{stock_code}'")
```

### 6.3 Input Validation

Pydantic으로 타입 검증:

```python
from pydantic import BaseModel, field_validator

class VerificationQuery(BaseModel):
    date: str
    market: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date must be YYYY-MM-DD format")
        return v
```

### 6.4 External API Keys

yfinance는 API key 불필요 (public data), 추가 보안 고려사항 없음.

---

## 7. Monitoring & Logging

### 7.1 Logger Pattern

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Verification started for %s market", market)
logger.error("Price fetch failed for %s: %s", stock_code, error)
logger.warning("Market closed on %s, skipping", date)
```

### 7.2 Audit Trail (verification_run_log)

모든 검증 실행 로그 저장:

```python
log = VerificationRunLog(
    run_date=target_date,
    market=market,
    status="success",
    stocks_verified=verified_count,
    stocks_failed=failed_count,
    duration_seconds=duration,
    error_details=None
)
db.add(log)
db.commit()
```

### 7.3 Health Check Endpoint

```python
@router.get("/status")
async def get_verification_status(db: Session = Depends(get_db)):
    """검증 시스템 상태 조회."""
    latest_kr = db.query(VerificationRunLog).filter(
        VerificationRunLog.market == "KR"
    ).order_by(VerificationRunLog.created_at.desc()).first()

    latest_us = db.query(VerificationRunLog).filter(
        VerificationRunLog.market == "US"
    ).order_by(VerificationRunLog.created_at.desc()).first()

    return {
        "status": "healthy" if latest_kr and latest_us else "degraded",
        "last_run": {
            "KR": {
                "date": str(latest_kr.run_date),
                "status": latest_kr.status,
                "stocks_verified": latest_kr.stocks_verified,
            } if latest_kr else None,
            "US": {
                "date": str(latest_us.run_date),
                "status": latest_us.status,
                "stocks_verified": latest_us.stocks_verified,
            } if latest_us else None,
        }
    }
```

---

## 8. Implementation Sequence (3 Phases)

### Phase 1: Backend Core (Day 1-2)

**Task:** DB models + processing logic.

**Files:**
- `backend/app/models/verification.py` (3 models)
- `backend/app/schemas/verification.py` (Pydantic schemas)
- `backend/app/collectors/price_fetcher.py` (yfinance wrapper)
- `backend/app/processing/verification_engine.py` (core logic)
- `backend/app/processing/theme_aggregator.py` (theme accuracy)

**Tests:**
- `backend/tests/unit/test_price_fetcher.py` (10 tests)
- `backend/tests/unit/test_verification_engine.py` (12 tests)
- `backend/tests/unit/test_theme_aggregator.py` (8 tests)
- `backend/tests/unit/test_verification_model.py` (7 tests)

**Verification:**
```bash
cd backend
.venv/bin/python -m pytest tests/unit/test_verification_*.py -v
```

### Phase 2: API + Scheduler (Day 3-4)

**Task:** REST API + scheduled jobs.

**Files:**
- `backend/app/api/verification.py` (7 endpoints)
- `backend/app/api/router.py` (modify: include verification router)
- `backend/app/collectors/verification_scheduler.py` (APScheduler)
- `backend/app/main.py` (modify: start verification scheduler)
- `backend/alembic/versions/xxxx_add_verification_tables.py` (migration)

**Tests:**
- `backend/tests/integration/test_api_verification.py` (14 tests)
- `backend/tests/integration/test_verification_scheduler.py` (4 tests)
- `backend/tests/integration/test_verification_pipeline.py` (10 tests)

**Verification:**
```bash
cd backend
.venv/bin/python -m pytest tests/integration/test_verification*.py -v
```

### Phase 3: Frontend (Day 5-6)

**Task:** UI dashboard.

**Files:**
- `frontend/src/pages/VerificationPage.tsx`
- `frontend/src/components/verification/AccuracyOverviewCard.tsx`
- `frontend/src/components/verification/DailyAccuracyChart.tsx`
- `frontend/src/components/verification/StockResultsTable.tsx`
- `frontend/src/components/verification/ThemeAccuracyBreakdown.tsx`
- `frontend/src/hooks/useVerification.ts`
- `frontend/src/api/verification.ts`
- `frontend/src/types/verification.ts`
- `frontend/src/App.tsx` (modify: add route)
- `frontend/src/components/layout/Sidebar.tsx` (modify: add nav item)

**Tests:**
- `frontend/tests/pages/VerificationPage.test.tsx` (7 tests)
- `frontend/tests/components/AccuracyChart.test.tsx` (5 tests)
- `frontend/tests/components/ThemeAccuracyTable.test.tsx` (6 tests)
- `frontend/tests/e2e/verification.spec.ts` (5 E2E tests)

**Verification:**
```bash
cd frontend
npx vitest run
npx playwright test tests/e2e/verification.spec.ts
```

---

## 9. Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                      External Dependencies                       │
│  - yfinance (주가 데이터)                                        │
│  - pandas-market-calendars (휴장일 체크)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Processing Layer                            │
│                                                                   │
│  price_fetcher.py  →  verification_engine.py  →  theme_aggregator│
│  (yfinance)           (예측 vs 실제 비교)         (테마 집계)    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer (READ-ONLY)                      │
│                                                                   │
│  news_event (READ)  →  prediction logic (READ)                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer (NEW)                         │
│                                                                   │
│  daily_prediction_result  ←  theme_prediction_accuracy           │
│  verification_run_log                                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer                                   │
│                                                                   │
│  /api/v1/verification/*  (7 endpoints)                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend                                    │
│                                                                   │
│  VerificationPage  →  AccuracyChart  →  ThemeAccuracyTable       │
└─────────────────────────────────────────────────────────────────┘
```

**Scheduler 독립 실행:**

```
APScheduler (main.py lifespan)
    │
    ├─ KR verification job (15:35 KST, mon-fri)
    │   └─ verification_engine.run_verification("KR")
    │
    └─ US verification job (16:30 EST, mon-fri)
        └─ verification_engine.run_verification("US")
```

---

## 10. Performance Considerations

### 10.1 Batch Price Downloads

**문제:** 100개 종목을 개별 호출하면 100 requests (느림 + rate limit).

**해결:**

```python
# Bad: 100 requests
for stock_code in stock_codes:
    price = yf.Ticker(format_ticker(stock_code)).history(period="5d")

# Good: 1 request
tickers = [format_ticker(c) for c in stock_codes]
df = yf.download(tickers, period="5d", progress=False, threads=True)
```

**권장 배치 크기:** 50 tickers per batch (yfinance 최적화 기준).

### 10.2 DB Batch Inserts

**문제:** 100개 종목을 개별 insert하면 100 transactions.

**해결:**

```python
# Bad: 100 commits
for result in results:
    db.add(result)
    db.commit()

# Good: 1 commit
for result in results:
    db.add(result)
db.commit()  # Batch commit

# Better: bulk_insert_mappings (SQLAlchemy 2.0)
db.bulk_insert_mappings(DailyPredictionResult, [
    {'stock_code': r['stock_code'], 'predicted_score': r['score'], ...}
    for r in results
])
db.commit()
```

### 10.3 Index Optimization

**Critical indexes (already defined):**

```sql
-- daily_prediction_result
CREATE INDEX idx_prediction_date_stock ON daily_prediction_result(prediction_date, stock_code);
CREATE INDEX idx_market_date ON daily_prediction_result(market, prediction_date);

-- theme_prediction_accuracy
CREATE INDEX idx_theme_date ON theme_prediction_accuracy(prediction_date, theme);
```

**Query pattern:**

```python
# Optimized: Uses idx_market_date
db.query(DailyPredictionResult).filter(
    DailyPredictionResult.market == "KR",
    DailyPredictionResult.prediction_date >= start_date,
    DailyPredictionResult.prediction_date <= end_date
).all()
```

### 10.4 Redis Caching (Optional)

**캐싱 대상:** 주가 데이터 (하루 동안 변경 없음).

```python
import redis
import json

redis_client = redis.from_url(settings.redis_url)

def fetch_price_with_cache(ticker: str, date: str) -> dict | None:
    cache_key = f"price:{ticker}:{date}"

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from yfinance
    price_data = fetch_actual_price(ticker)

    # Cache for 24 hours
    if price_data:
        redis_client.setex(cache_key, 86400, json.dumps(price_data))

    return price_data
```

### 10.5 Concurrent Processing

**문제:** KR + US 시장 순차 처리하면 느림.

**해결:** Separate scheduler jobs (parallel execution).

```python
# KR job runs at 15:35 KST
# US job runs at 16:30 EST
# They run independently (no blocking)
```

---

## 11. 구현 체크리스트

### Phase 1: Backend Core ✓

- [ ] `app/models/verification.py` — 3 models with Mapped[] pattern
- [ ] `app/schemas/verification.py` — Pydantic schemas with validators
- [ ] `app/collectors/price_fetcher.py` — yfinance wrapper + rate limiter
- [ ] `app/processing/verification_engine.py` — run_verification() + helpers
- [ ] `app/processing/theme_aggregator.py` — aggregate_theme_accuracy()
- [ ] Unit tests: `test_price_fetcher.py` (10), `test_verification_engine.py` (12), `test_theme_aggregator.py` (8)
- [ ] Coverage: 85%+

### Phase 2: API + Scheduler ✓

- [ ] `app/api/verification.py` — 7 endpoints with limiter
- [ ] `app/api/router.py` — include verification router
- [ ] `app/collectors/verification_scheduler.py` — APScheduler + CronTrigger
- [ ] `app/main.py` — start verification scheduler in lifespan
- [ ] `alembic/versions/xxxx_add_verification_tables.py` — migration script
- [ ] Integration tests: `test_api_verification.py` (14), `test_verification_scheduler.py` (4), `test_verification_pipeline.py` (10)
- [ ] Manual test: Trigger verification via POST `/api/v1/verification/run`

### Phase 3: Frontend ✓

- [ ] `src/pages/VerificationPage.tsx` — main page with filters
- [ ] `src/components/verification/AccuracyOverviewCard.tsx` — summary card
- [ ] `src/components/verification/DailyAccuracyChart.tsx` — Recharts line chart
- [ ] `src/components/verification/StockResultsTable.tsx` — sortable table
- [ ] `src/components/verification/ThemeAccuracyBreakdown.tsx` — bar chart
- [ ] `src/hooks/useVerification.ts` — TanStack Query hooks
- [ ] `src/api/verification.ts` — API client
- [ ] `src/types/verification.ts` — TypeScript types
- [ ] `src/App.tsx` — add `/verification` route
- [ ] `src/components/layout/Sidebar.tsx` — add nav item
- [ ] Component tests: 18 tests
- [ ] E2E tests: 5 tests
- [ ] Coverage: 80%+

---

## 12. 성공 기준

### Technical

- ✅ 모든 테스트 통과 (88 tests: 55 backend + 18 frontend + 10 integration + 5 E2E)
- ✅ Backend coverage ≥ 85%
- ✅ Frontend coverage ≥ 80%
- ✅ 타입 체크 통과 (mypy + tsc)
- ✅ Linter 통과 (ruff + eslint)

### Functional

- ✅ KR/US 시장 자동 검증 (daily)
- ✅ 정확도 계산 정확성 (manual verification with sample data)
- ✅ 테마별 집계 정확성
- ✅ API 응답 시간 < 2초 (cached queries)
- ✅ Frontend 로딩 < 3초

### Operational

- ✅ Scheduler 안정성 (7일 연속 성공 실행)
- ✅ Error handling (휴장일, 상장폐지 gracefully handled)
- ✅ Monitoring: `verification_run_log` 테이블 채워짐
- ✅ Rollback 가능 (feature flag + Alembic downgrade)

---

## 13. 향후 개선 사항

### Short-term (3개월)

1. **Confidence calibration analysis**
   - 예측 confidence와 실제 정확도 상관관계 분석
   - Confusion matrix 시각화

2. **Multi-day predictions**
   - 3일, 5일, 10일 예측 검증
   - 기간별 정확도 비교

3. **Feature importance analysis**
   - 어떤 뉴스 요소(sentiment, score, theme)가 정확도에 영향?
   - ML feature engineering 개선

### Long-term (6-12개월)

1. **Strategy backtesting**
   - 예측 기반 가상 매매 시뮬레이션
   - P&L tracking, Sharpe ratio

2. **Real-time price streaming**
   - WebSocket price feeds (Finnhub, Yahoo)
   - Intraday verification (장중 예측 검증)

3. **A/B testing framework**
   - 여러 예측 모델 비교
   - Champion/Challenger pattern

---

**END OF ARCHITECTURE ANALYSIS**
