# Prediction Verification System — TDD Test Plan

## Overview

This document defines the **Test-Driven Development (TDD)** test plan for the **Prediction Verification System** in StockNews. The system compares ML model predictions against actual stock price movements to calculate accuracy metrics by theme and stock.

**Core Principle:** NO CODE WITHOUT A FAILING TEST FIRST (RED-GREEN-REFACTOR).

---

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│  Prediction Verification System                              │
│                                                               │
│  1. Price Fetcher (yfinance) ─────┐                         │
│  2. Verification Engine            │→ Accuracy Calculation    │
│  3. Theme Aggregator               │                          │
│  4. DB Models (PredictionVerification) ────────────┐        │
│  5. API Endpoints (7 routes) ──────────────────────┤        │
│  6. Scheduler Integration                          │        │
│                                                     ↓        │
│                                            Frontend Dashboard │
│                                            - AccuracyChart    │
│                                            - ThemeAccuracyTable│
│                                            - VerificationPage │
└─────────────────────────────────────────────────────────────┘
```

---

## Test Framework

- **Backend:** pytest (existing pattern from `conftest.py`)
- **Frontend:** Vitest + React Testing Library + Playwright E2E
- **Coverage Targets:** Backend 85% | Frontend 80%

---

## Part 1: Backend Unit Tests (55 tests)

### 1.1 Price Fetcher Module (`app/collectors/price_fetcher.py`) — 10 tests

**Module:** `backend/tests/unit/test_price_fetcher.py`

| # | Test Name | What It Tests | Mock Data | Expected Result |
|---|-----------|---------------|-----------|-----------------|
| 1 | `test_fetch_actual_price_kr_stock` | Fetch actual price for Korean stock | yfinance returns 5-day price data for "005930.KS" | Returns dict with `actual_direction: "up"`, `price_change_pct: 3.5` |
| 2 | `test_fetch_actual_price_us_stock` | Fetch actual price for US stock | yfinance returns 5-day price data for "AAPL" | Returns dict with `actual_direction: "down"`, `price_change_pct: -2.1` |
| 3 | `test_fetch_actual_price_neutral` | Price change within ±1% threshold | Price change 0.5% | Returns `actual_direction: "neutral"` |
| 4 | `test_fetch_actual_price_empty_data` | Handle empty price data | yfinance returns empty DataFrame | Returns None |
| 5 | `test_fetch_actual_price_api_error` | Handle yfinance API error | yfinance raises Exception | Returns None (logs error) |
| 6 | `test_fetch_actual_price_holiday` | Skip market holidays | Request on 2024-12-25 (Christmas) | Returns None or uses last trading day |
| 7 | `test_fetch_actual_price_cache` | Cache mechanism works | Same stock called twice | yfinance API called once, second from cache |
| 8 | `test_fetch_actual_price_ticker_format` | Ticker formatting | Input "005930" vs "005930.KS" | Both resolve to "005930.KS" |
| 9 | `test_fetch_actual_price_custom_period` | Custom verification period (7d, 14d) | period=7 parameter | Compares day 0 vs day 7 prices |
| 10 | `test_fetch_batch_prices` | Batch fetch multiple stocks | List of 10 stock codes | Returns list of 10 results (with partial failures) |

**RED-GREEN-REFACTOR:**
```python
# RED: Write test first
def test_fetch_actual_price_kr_stock(mock_yfinance, sample_price_data):
    """한국 종목 실제 주가 방향 조회."""
    mock_ticker_instance = Mock()
    mock_ticker_instance.history.return_value = sample_price_data
    mock_yfinance.return_value = mock_ticker_instance

    result = fetch_actual_price("005930", prediction_date="2024-01-15")

    assert result is not None
    assert result["actual_direction"] in ["up", "down", "neutral"]
    assert "price_change_pct" in result
    mock_yfinance.assert_called_once_with("005930.KS")

# GREEN: Implement minimal code
def fetch_actual_price(stock_code, prediction_date):
    # Implementation here
    pass

# REFACTOR: Clean up, optimize
```

---

### 1.2 Verification Engine (`app/processing/verification.py`) — 12 tests

**Module:** `backend/tests/unit/test_verification_engine.py`

| # | Test Name | What It Tests | Mock Data | Expected Result |
|---|-----------|---------------|-----------|-----------------|
| 11 | `test_verify_single_prediction_correct` | Correct prediction (up == up) | Predicted "up", actual "up" | `is_correct=True`, `accuracy=1.0` |
| 12 | `test_verify_single_prediction_incorrect` | Incorrect prediction (up != down) | Predicted "up", actual "down" | `is_correct=False`, `accuracy=0.0` |
| 13 | `test_verify_single_prediction_neutral_tolerance` | Neutral with tolerance | Predicted "up", actual "neutral" | Configurable: strict (wrong) vs lenient (half-credit) |
| 14 | `test_verify_batch_predictions` | Batch verification | 100 predictions with mock prices | Returns list of 100 VerificationResult objects |
| 15 | `test_calculate_accuracy_by_stock` | Per-stock accuracy | 5 predictions for "005930": 4 correct | Returns {"005930": 0.8} |
| 16 | `test_calculate_accuracy_by_theme` | Per-theme accuracy | Theme "반도체": 10/12 correct | Returns {"반도체": 0.833} |
| 17 | `test_calculate_accuracy_by_direction` | Accuracy per direction | "up": 20/30, "down": 15/20 | Returns {"up": 0.667, "down": 0.75} |
| 18 | `test_verify_missing_actual_data` | Handle missing price data | Predicted "up", actual=None | Skips (not counted as wrong) |
| 19 | `test_verify_confidence_weighting` | Weight by prediction confidence | High confidence wrong hurts more | Weighted accuracy < unweighted |
| 20 | `test_verify_time_decay` | Recent predictions weight more | 30-day window with decay | Recent predictions contribute more |
| 21 | `test_verify_empty_predictions` | No predictions to verify | Empty list | Returns empty results, accuracy=None |
| 22 | `test_verify_all_neutral` | All predictions neutral | 10 neutral predictions, 5 actual neutral | Accuracy depends on tolerance mode |

**Example Test:**
```python
def test_verify_single_prediction_correct(db_session):
    """예측 정확도 검증 — 맞은 경우."""
    engine = VerificationEngine(db_session)

    prediction = {
        "stock_code": "005930",
        "predicted_direction": "up",
        "prediction_date": "2024-01-15",
        "confidence": 0.8,
    }

    actual = {
        "actual_direction": "up",
        "price_change_pct": 3.5,
    }

    result = engine.verify_single(prediction, actual)

    assert result.is_correct is True
    assert result.accuracy == 1.0
    assert result.stock_code == "005930"
```

---

### 1.3 Theme Aggregator (`app/processing/theme_aggregator.py`) — 8 tests

**Module:** `backend/tests/unit/test_theme_aggregator.py`

| # | Test Name | What It Tests | Mock Data | Expected Result |
|---|-----------|---------------|-----------|-----------------|
| 23 | `test_aggregate_by_theme_basic` | Group by theme | 20 verifications across 3 themes | Returns {"반도체": 0.85, "자동차": 0.6, "바이오": 0.9} |
| 24 | `test_aggregate_by_theme_single` | Single theme | All verifications same theme | Returns single theme accuracy |
| 25 | `test_aggregate_by_theme_empty` | Empty verifications | Empty list | Returns empty dict |
| 26 | `test_aggregate_by_theme_min_samples` | Filter low-sample themes | Theme with only 2 predictions | Excluded if min_samples=5 |
| 27 | `test_aggregate_by_date_range` | Date range filtering | 30-day verifications, query 7-day | Returns only last 7 days |
| 28 | `test_aggregate_by_market` | Separate KR/US markets | Mixed KR and US stocks | Returns {"KR": {...}, "US": {...}} |
| 29 | `test_aggregate_multi_day_average` | Multi-day average | 30 days of daily aggregates | Returns smoothed 7-day moving average |
| 30 | `test_aggregate_confidence_filter` | Filter by confidence threshold | Only include confidence >= 0.7 | Low confidence predictions excluded |

**Example Test:**
```python
def test_aggregate_by_theme_basic(db_session, sample_verifications):
    """테마별 정확도 집계."""
    aggregator = ThemeAggregator(db_session)

    # sample_verifications: 10 반도체 (8 correct), 10 자동차 (6 correct)
    results = aggregator.aggregate_by_theme(sample_verifications)

    assert results["반도체"]["accuracy"] == 0.8
    assert results["반도체"]["count"] == 10
    assert results["자동차"]["accuracy"] == 0.6
    assert results["자동차"]["count"] == 10
```

---

### 1.4 DB Models (`app/models/prediction_verification.py`) — 7 tests

**Module:** `backend/tests/unit/test_verification_model.py`

| # | Test Name | What It Tests | Mock Data | Expected Result |
|---|-----------|---------------|-----------|-----------------|
| 31 | `test_create_verification_record` | Insert new record | Valid verification data | Record saved with auto-generated ID |
| 32 | `test_verification_unique_constraint` | Prevent duplicates | Same stock_code + prediction_date twice | Second insert raises IntegrityError |
| 33 | `test_verification_nullable_fields` | Handle NULL actual data | actual_direction=None | Record saved with NULL (not verified yet) |
| 34 | `test_verification_cascade_delete` | Foreign key cascade | Delete related NewsEvent | Verification records also deleted (or set NULL) |
| 35 | `test_verification_query_by_date` | Date range query | Query 2024-01-01 to 2024-01-31 | Returns only January records |
| 36 | `test_verification_query_by_theme` | Theme filtering | Query theme="반도체" | Returns only semiconductor verifications |
| 37 | `test_verification_index_performance` | Index usage | Query 100k records by stock_code | Uses index, query < 50ms |

**Schema:**
```python
class PredictionVerification(Base):
    __tablename__ = "prediction_verifications"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100))
    theme = Column(String(50), index=True)
    market = Column(String(10))  # "KR" | "US"

    prediction_date = Column(Date, nullable=False, index=True)
    predicted_direction = Column(String(10))  # "up" | "down" | "neutral"
    prediction_score = Column(Float)
    confidence = Column(Float)

    verification_date = Column(Date)  # When actual price was fetched
    actual_direction = Column(String(10))
    price_change_pct = Column(Float)
    is_correct = Column(Boolean)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "prediction_date", name="uq_stock_prediction_date"),
        Index("ix_verification_theme_date", "theme", "verification_date"),
    )
```

**Example Test:**
```python
def test_create_verification_record(db_session):
    """검증 레코드 생성."""
    verification = PredictionVerification(
        stock_code="005930",
        stock_name="삼성전자",
        theme="반도체",
        market="KR",
        prediction_date=date(2024, 1, 15),
        predicted_direction="up",
        prediction_score=85.0,
        confidence=0.8,
    )

    db_session.add(verification)
    db_session.commit()

    assert verification.id is not None
    assert verification.created_at is not None
```

---

### 1.5 API Endpoints (`app/api/verification.py`) — 14 tests

**Module:** `backend/tests/integration/test_api_verification.py`

| # | Test Name | What It Tests | Mock Data | Expected Result |
|---|-----------|---------------|-----------|-----------------|
| 38 | `test_get_verification_summary` | GET /api/v1/verification/summary | DB with 100 verifications | Returns overall accuracy, total count |
| 39 | `test_get_verification_by_stock` | GET /api/v1/verification/{code} | Stock "005930" with 20 verifications | Returns list of verifications for stock |
| 40 | `test_get_verification_by_theme` | GET /api/v1/verification/theme/{theme} | Theme "반도체" with 50 verifications | Returns theme accuracy + list |
| 41 | `test_get_verification_timeline` | GET /api/v1/verification/timeline | 30 days of daily accuracy | Returns [{date, accuracy, count}, ...] |
| 42 | `test_get_theme_accuracy_ranking` | GET /api/v1/verification/themes/ranking | 10 themes with different accuracy | Returns sorted list (best → worst) |
| 43 | `test_get_verification_by_date` | GET /api/v1/verification?date=2024-01-15 | Specific date | Returns verifications for that date |
| 44 | `test_get_verification_pagination` | GET /api/v1/verification?offset=20&limit=10 | 100 records | Returns 10 records starting from 20 |
| 45 | `test_post_trigger_verification` | POST /api/v1/verification/trigger | Manual trigger | Starts async verification task, returns job_id |
| 46 | `test_verification_summary_empty` | GET /api/v1/verification/summary (no data) | Empty DB | Returns accuracy=None, count=0 |
| 47 | `test_verification_invalid_stock` | GET /api/v1/verification/999999 | Unknown stock | Returns 200 with empty list |
| 48 | `test_verification_date_range` | GET /api/v1/verification?start=...&end=... | Date range filter | Returns only records in range |
| 49 | `test_verification_market_filter` | GET /api/v1/verification?market=KR | Market filter | Returns only KR stocks |
| 50 | `test_verification_confidence_filter` | GET /api/v1/verification?min_confidence=0.7 | Confidence filter | Returns only high-confidence predictions |
| 51 | `test_verification_rate_limit` | 100 requests in 1 minute | Rate limit test | 61st request returns 429 |

**Example Test:**
```python
@pytest.mark.asyncio
async def test_get_verification_summary(async_client, db_session, sample_verifications):
    """GET /api/v1/verification/summary → 200 + 전체 정확도."""
    resp = await async_client.get("/api/v1/verification/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_accuracy" in data
    assert "total_predictions" in data
    assert "correct_predictions" in data
    assert 0 <= data["overall_accuracy"] <= 1.0
```

---

### 1.6 Scheduler Integration (`app/schedulers/verification_scheduler.py`) — 4 tests

**Module:** `backend/tests/integration/test_verification_scheduler.py`

| # | Test Name | What It Tests | Mock Data | Expected Result |
|---|-----------|---------------|-----------|-----------------|
| 52 | `test_scheduled_verification_runs` | Scheduler triggers verification job | Cron: daily at 18:00 | Job runs, verifies all pending predictions |
| 53 | `test_verification_batch_processing` | Process 1000 predictions | Large batch | Processes in chunks of 100, all complete |
| 54 | `test_verification_failure_retry` | Retry on transient failure | Price API fails 2x, succeeds 3x | Retries with exponential backoff |
| 55 | `test_verification_partial_failure` | Handle partial batch failure | 100 predictions, 10 price API errors | 90 verified, 10 skipped (logged) |

**Example Test:**
```python
def test_scheduled_verification_runs(db_session, mock_price_api):
    """스케줄러가 검증 작업을 실행."""
    # Create pending predictions (5 days old, not verified yet)
    for i in range(10):
        prediction = PredictionVerification(
            stock_code=f"00593{i}",
            prediction_date=date.today() - timedelta(days=5),
            predicted_direction="up",
        )
        db_session.add(prediction)
    db_session.commit()

    # Run scheduler job
    scheduler = VerificationScheduler(db_session)
    scheduler.run_daily_verification()

    # Verify all predictions now have actual_direction
    verifications = db_session.query(PredictionVerification).all()
    assert all(v.actual_direction is not None for v in verifications)
```

---

## Part 2: Backend Integration Tests (10 tests)

**Module:** `backend/tests/integration/test_verification_pipeline.py`

| # | Test Name | What It Tests | Expected Result |
|---|-----------|---------------|-----------------|
| 56 | `test_full_verification_pipeline` | End-to-end: predict → wait 5 days → verify | All components work together |
| 57 | `test_verification_with_db_rollback` | Transaction rollback on error | No partial data on failure |
| 58 | `test_verification_with_redis_cache` | Price data cached in Redis | Second verification uses cache |
| 59 | `test_verification_concurrent_requests` | 10 simultaneous API requests | No race conditions, all succeed |
| 60 | `test_verification_theme_aggregation_accuracy` | Aggregate 100 verifications by theme | Matches manual calculation |
| 61 | `test_verification_timeline_consistency` | Daily accuracy matches summary | Timeline sum == overall accuracy |
| 62 | `test_verification_export_csv` | Export verifications to CSV | Valid CSV with all fields |
| 63 | `test_verification_import_historical` | Import historical verifications | Bulk insert 10k records |
| 64 | `test_verification_api_auth` | Protected endpoints require auth | 401 without token (if auth enabled) |
| 65 | `test_verification_cross_market` | KR and US predictions separate | No cross-contamination |

**Example Test:**
```python
@pytest.mark.asyncio
async def test_full_verification_pipeline(async_client, db_session, mock_price_api):
    """전체 검증 파이프라인 통합 테스트."""
    # 1. Create predictions via prediction API
    resp = await async_client.get("/api/v1/stocks/005930/prediction")
    assert resp.status_code == 200

    # 2. Wait (mock 5 days later)
    # 3. Trigger verification
    resp = await async_client.post("/api/v1/verification/trigger")
    assert resp.status_code == 202  # Accepted

    # 4. Check verification results
    resp = await async_client.get("/api/v1/verification/005930")
    assert resp.status_code == 200
    verifications = resp.json()
    assert len(verifications) > 0
    assert verifications[0]["is_correct"] is not None
```

---

## Part 3: Frontend Unit Tests (18 tests)

### 3.1 VerificationPage Component — 7 tests

**Module:** `frontend/tests/pages/VerificationPage.test.tsx`

| # | Test Name | What It Tests | Expected Result |
|---|-----------|---------------|-----------------|
| 66 | `test_verification_page_renders` | Component renders | Page heading "예측 검증" visible |
| 67 | `test_verification_page_loading` | Shows loading state | Spinner visible while loading |
| 68 | `test_verification_page_data` | Displays verification data | Summary, chart, and table render |
| 69 | `test_verification_page_error` | Handles API error | Error message displayed |
| 70 | `test_verification_date_picker` | Date range picker works | Updates data on date change |
| 71 | `test_verification_market_selector` | Market selector (KR/US) | Switches between KR and US data |
| 72 | `test_verification_export_button` | Export CSV button | Downloads CSV file |

**Example Test:**
```tsx
describe('VerificationPage', () => {
  it('renders verification page heading', () => {
    renderWithProviders(<VerificationPage />);
    expect(screen.getByText('예측 검증')).toBeInTheDocument();
  });

  it('displays verification summary', async () => {
    renderWithProviders(<VerificationPage />);
    await waitFor(() => {
      expect(screen.getByText('전체 정확도')).toBeInTheDocument();
    });
    expect(screen.getByText(/\d+\.\d+%/)).toBeInTheDocument();
  });
});
```

---

### 3.2 AccuracyChart Component — 5 tests

**Module:** `frontend/tests/components/AccuracyChart.test.tsx`

| # | Test Name | What It Tests | Expected Result |
|---|-----------|---------------|-----------------|
| 73 | `test_accuracy_chart_renders` | Line chart renders | Recharts container visible |
| 74 | `test_accuracy_chart_data` | Displays timeline data | Line with 30 data points |
| 75 | `test_accuracy_chart_tooltip` | Tooltip on hover | Shows date and accuracy |
| 76 | `test_accuracy_chart_empty` | Empty state | "데이터가 없습니다" message |
| 77 | `test_accuracy_chart_period_selector` | Switch periods (7d, 30d, 90d) | Updates chart data |

**Example Test:**
```tsx
describe('AccuracyChart', () => {
  it('renders chart with data', () => {
    const data = [
      { date: '2024-01-01', accuracy: 0.75, count: 20 },
      { date: '2024-01-02', accuracy: 0.80, count: 25 },
    ];
    const { container } = render(<AccuracyChart data={data} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    render(<AccuracyChart data={[]} />);
    expect(screen.getByText('데이터가 없습니다')).toBeInTheDocument();
  });
});
```

---

### 3.3 ThemeAccuracyTable Component — 6 tests

**Module:** `frontend/tests/components/ThemeAccuracyTable.test.tsx`

| # | Test Name | What It Tests | Expected Result |
|---|-----------|---------------|-----------------|
| 78 | `test_theme_table_renders` | Table renders | Headers: 테마, 정확도, 예측수 |
| 79 | `test_theme_table_data` | Displays theme rows | 10 theme rows with accuracy |
| 80 | `test_theme_table_sorting` | Sort by accuracy | Clicking header sorts DESC |
| 81 | `test_theme_table_color_coding` | Color by accuracy | >80% green, <60% red |
| 82 | `test_theme_table_empty` | Empty state | "테마 데이터가 없습니다" |
| 83 | `test_theme_table_click_theme` | Click theme navigates | Navigates to /verification/theme/{theme} |

**Example Test:**
```tsx
describe('ThemeAccuracyTable', () => {
  const mockThemes = [
    { theme: '반도체', accuracy: 0.85, count: 50 },
    { theme: '자동차', accuracy: 0.60, count: 30 },
  ];

  it('renders table with theme data', () => {
    render(<ThemeAccuracyTable themes={mockThemes} />);
    expect(screen.getByText('반도체')).toBeInTheDocument();
    expect(screen.getByText('85.0%')).toBeInTheDocument();
  });

  it('color codes accuracy levels', () => {
    const { container } = render(<ThemeAccuracyTable themes={mockThemes} />);
    const highAccuracy = screen.getByText('85.0%').closest('td');
    expect(highAccuracy).toHaveClass('text-green-600');
  });
});
```

---

## Part 4: Frontend E2E Tests (5 tests)

**Module:** `frontend/tests/e2e/verification.spec.ts`

| # | Test Name | What It Tests | Expected Result |
|---|-----------|---------------|-----------------|
| 84 | `test_e2e_navigate_to_verification` | Navigate from dashboard | Click "예측 검증" → page loads |
| 85 | `test_e2e_view_verification_summary` | View summary | Summary card displays accuracy |
| 86 | `test_e2e_filter_by_date_range` | Date range filter | Select last 7 days → chart updates |
| 87 | `test_e2e_click_theme_detail` | Theme drill-down | Click theme → theme detail page |
| 88 | `test_e2e_responsive_design` | Mobile responsive | Test on 375px width, all content visible |

**Example Test:**
```typescript
test('user can view verification summary', async ({ page }) => {
  await page.goto('/verification');

  // Wait for data to load
  await page.waitForSelector('text=전체 정확도');

  // Check summary displays
  const accuracy = await page.locator('[data-testid="overall-accuracy"]').textContent();
  expect(accuracy).toMatch(/\d+\.\d+%/);

  // Check chart renders
  await expect(page.locator('.recharts-responsive-container')).toBeVisible();
});
```

---

## Coverage Targets

### Backend Coverage

| Module | Target | Critical Paths |
|--------|--------|----------------|
| `price_fetcher.py` | 90% | API errors, cache, ticker format |
| `verification.py` | 90% | Accuracy calculation, batch processing |
| `theme_aggregator.py` | 85% | Grouping logic, edge cases |
| `verification_model.py` | 80% | CRUD, constraints |
| `api/verification.py` | 85% | All endpoints, error handling |
| **Overall** | **85%** | **All test branches** |

### Frontend Coverage

| Module | Target | Critical Paths |
|--------|--------|----------------|
| `VerificationPage.tsx` | 80% | Loading, data, error states |
| `AccuracyChart.tsx` | 80% | Data rendering, empty state |
| `ThemeAccuracyTable.tsx` | 80% | Sorting, color coding |
| **Overall** | **80%** | **All user interactions** |

---

## Test Execution Commands

### Backend

```bash
# All tests
cd backend
.venv/bin/python -m pytest

# Unit tests only
.venv/bin/python -m pytest tests/unit/

# Integration tests only
.venv/bin/python -m pytest tests/integration/

# Verification tests only
.venv/bin/python -m pytest tests/unit/test_price_fetcher.py
.venv/bin/python -m pytest tests/unit/test_verification_engine.py
.venv/bin/python -m pytest tests/integration/test_verification_pipeline.py

# Coverage report
.venv/bin/python -m pytest --cov=app --cov-report=html --cov-report=term-missing

# Watch mode (requires pytest-watch)
.venv/bin/python -m ptw -- -v
```

### Frontend

```bash
# All tests
cd frontend
npm test

# Unit tests only
npx vitest run

# E2E tests only
npx playwright test tests/e2e/verification.spec.ts

# Coverage report
npx vitest run --coverage

# Watch mode
npx vitest
```

---

## TDD Workflow: RED-GREEN-REFACTOR

### Phase 1: Price Fetcher (Tests 1-10)

**RED (Write failing test):**
```python
def test_fetch_actual_price_kr_stock(mock_yfinance, sample_price_data):
    """한국 종목 실제 주가 방향 조회."""
    result = fetch_actual_price("005930", prediction_date="2024-01-15")
    assert result["actual_direction"] in ["up", "down", "neutral"]
    # ❌ FAILS — fetch_actual_price not implemented
```

**GREEN (Make it pass):**
```python
def fetch_actual_price(stock_code, prediction_date):
    """Minimal implementation to pass test."""
    ticker = format_ticker(stock_code)
    data = yf.Ticker(ticker).history(period="5d")
    if data.empty:
        return None

    start_price = data.iloc[0]["Close"]
    end_price = data.iloc[-1]["Close"]
    change_pct = (end_price - start_price) / start_price * 100

    if change_pct > 1.0:
        direction = "up"
    elif change_pct < -1.0:
        direction = "down"
    else:
        direction = "neutral"

    return {
        "actual_direction": direction,
        "price_change_pct": round(change_pct, 2),
    }
    # ✅ PASSES
```

**REFACTOR (Improve):**
```python
def fetch_actual_price(
    stock_code: str,
    prediction_date: str,
    period: int = 5,
    threshold: float = 1.0,
) -> dict | None:
    """
    Fetch actual price movement after prediction date.

    Args:
        stock_code: Stock code (e.g., "005930" or "AAPL")
        prediction_date: Date when prediction was made
        period: Number of days to verify (default 5)
        threshold: % threshold for neutral (default 1.0%)

    Returns:
        Dict with actual_direction and price_change_pct, or None if no data
    """
    try:
        ticker = _format_ticker(stock_code)
        data = yf.Ticker(ticker).history(period=f"{period}d")

        if data.empty or len(data) < 2:
            logger.warning(f"No price data for {stock_code}")
            return None

        start_price = data.iloc[0]["Close"]
        end_price = data.iloc[-1]["Close"]
        change_pct = (end_price - start_price) / start_price * 100

        direction = _classify_direction(change_pct, threshold)

        return {
            "actual_direction": direction,
            "price_change_pct": round(change_pct, 2),
        }
    except Exception as e:
        logger.error(f"Error fetching price for {stock_code}: {e}")
        return None

def _classify_direction(change_pct: float, threshold: float) -> str:
    """Classify price change as up/down/neutral."""
    if change_pct > threshold:
        return "up"
    elif change_pct < -threshold:
        return "down"
    else:
        return "neutral"

def _format_ticker(stock_code: str) -> str:
    """Format stock code to yfinance ticker."""
    if stock_code.endswith((".KS", ".KQ")):
        return stock_code
    if stock_code.isdigit() and len(stock_code) == 6:
        return f"{stock_code}.KS"  # Korean stock
    return stock_code  # US stock
    # ✅ Clean, tested, documented
```

### Phase 2: Verification Engine (Tests 11-22)

**Repeat RED-GREEN-REFACTOR** for each test case.

### Phase 3: Theme Aggregator (Tests 23-30)

**Repeat RED-GREEN-REFACTOR** for each test case.

### Phase 4: DB Models (Tests 31-37)

**RED (Schema + test):**
```python
def test_create_verification_record(db_session):
    """검증 레코드 생성."""
    verification = PredictionVerification(
        stock_code="005930",
        prediction_date=date(2024, 1, 15),
        predicted_direction="up",
    )
    db_session.add(verification)
    db_session.commit()
    assert verification.id is not None
    # ❌ FAILS — PredictionVerification not defined
```

**GREEN (Create model):**
```python
class PredictionVerification(Base):
    __tablename__ = "prediction_verifications"
    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False)
    prediction_date = Column(Date, nullable=False)
    predicted_direction = Column(String(10))
    # ✅ PASSES
```

**REFACTOR (Add all fields, constraints, indexes):**
```python
class PredictionVerification(Base):
    __tablename__ = "prediction_verifications"

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(100))
    theme = Column(String(50), index=True)
    market = Column(String(10))

    prediction_date = Column(Date, nullable=False, index=True)
    predicted_direction = Column(String(10))
    prediction_score = Column(Float)
    confidence = Column(Float)

    verification_date = Column(Date)
    actual_direction = Column(String(10))
    price_change_pct = Column(Float)
    is_correct = Column(Boolean)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_code", "prediction_date", name="uq_stock_prediction_date"),
        Index("ix_verification_theme_date", "theme", "verification_date"),
    )
    # ✅ Production-ready
```

### Phase 5: API Endpoints (Tests 38-51)

**RED (Write integration test):**
```python
@pytest.mark.asyncio
async def test_get_verification_summary(async_client):
    """GET /api/v1/verification/summary → 200."""
    resp = await async_client.get("/api/v1/verification/summary")
    assert resp.status_code == 200
    # ❌ FAILS — Endpoint not implemented
```

**GREEN (Implement endpoint):**
```python
@router.get("/api/v1/verification/summary")
async def get_verification_summary(db: Session = Depends(get_db)):
    verifications = db.query(PredictionVerification).all()
    total = len(verifications)
    correct = sum(1 for v in verifications if v.is_correct)
    return {
        "overall_accuracy": correct / total if total > 0 else None,
        "total_predictions": total,
        "correct_predictions": correct,
    }
    # ✅ PASSES
```

**REFACTOR (Add caching, error handling, query optimization):**
```python
@router.get("/api/v1/verification/summary")
@limiter.limit("60/minute")
async def get_verification_summary(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    start_date: str | None = None,
    end_date: str | None = None,
    market: str | None = None,
):
    """전체 검증 요약 통계."""
    query = db.query(PredictionVerification).filter(
        PredictionVerification.actual_direction.isnot(None)
    )

    if start_date:
        query = query.filter(PredictionVerification.verification_date >= start_date)
    if end_date:
        query = query.filter(PredictionVerification.verification_date <= end_date)
    if market:
        query = query.filter(PredictionVerification.market == market)

    # Use SQL aggregation instead of loading all records
    total = query.count()
    correct = query.filter(PredictionVerification.is_correct == True).count()

    return {
        "overall_accuracy": round(correct / total, 4) if total > 0 else None,
        "total_predictions": total,
        "correct_predictions": correct,
        "incorrect_predictions": total - correct,
    }
    # ✅ Optimized, filtered, rate-limited
```

### Phase 6: Frontend Components (Tests 66-83)

**RED (Write component test):**
```tsx
describe('VerificationPage', () => {
  it('displays verification summary', async () => {
    renderWithProviders(<VerificationPage />);
    await waitFor(() => {
      expect(screen.getByText('전체 정확도')).toBeInTheDocument();
    });
    // ❌ FAILS — Component not implemented
  });
});
```

**GREEN (Implement component):**
```tsx
export default function VerificationPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['verification', 'summary'],
    queryFn: () => fetch('/api/v1/verification/summary').then(r => r.json()),
  });

  if (isLoading) return <div>로딩 중...</div>;

  return (
    <div>
      <h1>예측 검증</h1>
      <div>전체 정확도: {data.overall_accuracy}%</div>
    </div>
  );
  // ✅ PASSES
}
```

**REFACTOR (Add styling, error handling, full layout):**
```tsx
export default function VerificationPage() {
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [market, setMarket] = useState<'KR' | 'US'>('KR');

  const { data, isLoading, error } = useQuery({
    queryKey: ['verification', 'summary', dateRange, market],
    queryFn: () => fetchVerificationSummary({ ...dateRange, market }),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error.message} />;

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">예측 검증</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <DateRangePicker value={dateRange} onChange={setDateRange} />
        <MarketSelector value={market} onChange={setMarket} />
      </div>

      <SummaryCard
        accuracy={data.overall_accuracy}
        total={data.total_predictions}
        correct={data.correct_predictions}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <AccuracyChart data={data.timeline} />
        <ThemeAccuracyTable themes={data.themes} />
      </div>
    </div>
  );
  // ✅ Production UI
}
```

---

## Test Data Fixtures

### Backend Fixtures (add to `conftest.py`)

```python
@pytest.fixture
def sample_predictions(db_session):
    """테스트용 예측 데이터 50건."""
    predictions = []
    for i in range(50):
        pred = PredictionVerification(
            stock_code=f"00593{i % 10}",
            stock_name=f"테스트종목{i % 10}",
            theme=["반도체", "자동차", "바이오"][i % 3],
            market="KR",
            prediction_date=date.today() - timedelta(days=i),
            predicted_direction=["up", "down", "neutral"][i % 3],
            prediction_score=random.uniform(40, 90),
            confidence=random.uniform(0.5, 0.95),
        )
        db_session.add(pred)
        predictions.append(pred)

    db_session.commit()
    return predictions

@pytest.fixture
def sample_verifications(db_session, sample_predictions):
    """검증 완료된 예측 데이터."""
    for pred in sample_predictions:
        pred.verification_date = pred.prediction_date + timedelta(days=5)
        pred.actual_direction = random.choice(["up", "down", "neutral"])
        pred.price_change_pct = random.uniform(-5, 5)
        pred.is_correct = (pred.predicted_direction == pred.actual_direction)

    db_session.commit()
    return sample_predictions

@pytest.fixture
def mock_price_api(monkeypatch):
    """yfinance API mock."""
    def mock_history(period):
        dates = pd.date_range(end=date.today(), periods=5, freq="D")
        return pd.DataFrame({
            "Open": [100 + i for i in range(5)],
            "Close": [102 + i for i in range(5)],
        }, index=dates)

    mock_ticker = Mock()
    mock_ticker.history.side_effect = mock_history
    monkeypatch.setattr("app.collectors.price_fetcher.yf.Ticker", lambda x: mock_ticker)
    return mock_ticker
```

### Frontend Fixtures (MSW handlers)

```typescript
// tests/mocks/handlers.ts
export const verificationHandlers = [
  http.get('/api/v1/verification/summary', () => {
    return HttpResponse.json({
      overall_accuracy: 0.7523,
      total_predictions: 150,
      correct_predictions: 113,
      incorrect_predictions: 37,
    });
  }),

  http.get('/api/v1/verification/timeline', () => {
    const timeline = Array.from({ length: 30 }, (_, i) => ({
      date: `2024-01-${String(i + 1).padStart(2, '0')}`,
      accuracy: 0.6 + Math.random() * 0.3,
      count: Math.floor(Math.random() * 50) + 10,
    }));
    return HttpResponse.json(timeline);
  }),

  http.get('/api/v1/verification/themes/ranking', () => {
    return HttpResponse.json([
      { theme: '반도체', accuracy: 0.85, count: 50 },
      { theme: '자동차', accuracy: 0.72, count: 30 },
      { theme: '바이오', accuracy: 0.68, count: 25 },
    ]);
  }),
];
```

---

## Test Pyramid

```
        E2E (5 tests)
       /             \
      /   Integration  \
     /     (10 tests)   \
    /                    \
   /       Unit Tests     \
  /       (73 tests)       \
 /__________________________\
```

**Ratio:** 73 unit : 10 integration : 5 E2E ≈ 83% : 11% : 6%

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test-verification.yml
name: Verification Tests

on:
  push:
    paths:
      - 'backend/app/collectors/price_fetcher.py'
      - 'backend/app/processing/verification.py'
      - 'backend/app/api/verification.py'
      - 'backend/tests/**/*verification*.py'
      - 'frontend/src/**/*Verification*.tsx'
      - 'frontend/tests/**/*verification*.ts*'

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: cd backend && pip install -e .
      - run: cd backend && pytest tests/unit/test_verification_*.py --cov --cov-fail-under=85

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm test -- --coverage --run
```

---

## Success Criteria

✅ **All 88 tests pass** (55 backend unit + 10 integration + 18 frontend + 5 E2E)
✅ **Backend coverage ≥ 85%**
✅ **Frontend coverage ≥ 80%**
✅ **No test commits without RED phase** (enforce in code review)
✅ **All API endpoints have integration tests**
✅ **All edge cases covered** (null, empty, errors)
✅ **CI pipeline green**

---

## Next Steps

1. **Implement Price Fetcher** (Tests 1-10) — RED-GREEN-REFACTOR
2. **Implement Verification Engine** (Tests 11-22) — RED-GREEN-REFACTOR
3. **Implement Theme Aggregator** (Tests 23-30) — RED-GREEN-REFACTOR
4. **Create DB Models** (Tests 31-37) — RED-GREEN-REFACTOR
5. **Build API Endpoints** (Tests 38-51) — RED-GREEN-REFACTOR
6. **Add Scheduler** (Tests 52-55) — RED-GREEN-REFACTOR
7. **Integration Tests** (Tests 56-65)
8. **Frontend Components** (Tests 66-83) — RED-GREEN-REFACTOR
9. **E2E Tests** (Tests 84-88)
10. **Coverage Verification** — Run `pytest --cov` and `vitest --coverage`

---

**Remember: NO CODE WITHOUT A FAILING TEST FIRST. Tests are not optional.**
