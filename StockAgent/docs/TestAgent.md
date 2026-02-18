# TestAgent v1.0

## StockAgent TDD 기반 테스트 계획서

---

# 1. 개요

TestAgent는 StockAgent 개발 전 과정에서 TDD(Test-Driven Development) 방법론을 적용하기 위한 테스트 SubAgent 가이드이다.

모든 개발 태스크(B-1~B-22, F-1~F-14)에 대해 **테스트를 먼저 작성**하고, 구현 코드가 테스트를 통과하는 방식으로 진행한다.

### TDD 사이클

```
RED   → 실패하는 테스트 작성
GREEN → 테스트를 통과하는 최소 구현
REFACTOR → 코드 품질 개선 (테스트 유지)
```

### 핵심 원칙

* 구현 코드 작성 전에 반드시 테스트부터 작성
* 커버리지 목표: Backend 80%+, Frontend 70%+
* 모든 public 함수에 대한 테스트 필수
* Happy path + Edge case + Error path 모두 커버
* Mock을 활용한 외부 의존성 격리

---

# 2. 테스트 기술 스택

## 2.1 Backend

| 도구 | 용도 |
|------|------|
| pytest | 테스트 프레임워크 |
| pytest-asyncio | async 함수 테스트 |
| pytest-cov | 커버리지 리포트 |
| httpx (MockTransport) | HTTP 클라이언트 Mock |
| respx | httpx 요청 Mock |
| factory-boy | 테스트 데이터 팩토리 |
| testcontainers | PostgreSQL/Redis 컨테이너 테스트 |
| fakeredis | Redis Mock |
| SQLAlchemy (in-memory SQLite) | DB 단위 테스트용 |

## 2.2 Frontend

| 도구 | 용도 |
|------|------|
| Jest | 테스트 프레임워크 |
| React Testing Library | 컴포넌트 테스트 |
| MSW (Mock Service Worker) | API Mock |
| Playwright | E2E 테스트 |
| jest-websocket-mock | WebSocket Mock |

---

# 3. 테스트 디렉토리 구조

```
StockAgent/
├── backend/
│   └── tests/
│       ├── conftest.py              # 공통 fixture (DB, Redis, httpx client)
│       ├── factories.py             # factory-boy 데이터 팩토리
│       │
│       ├── unit/                    # 단위 테스트
│       │   ├── kiwoom_client/
│       │   │   ├── test_auth.py         # T-B3: 인증
│       │   │   ├── test_market.py       # T-B4: 시세
│       │   │   ├── test_order.py        # T-B5: 주문
│       │   │   └── test_account.py      # T-B6: 계좌
│       │   │
│       │   ├── core/
│       │   │   ├── test_market_data.py  # T-B7: 시세 수집
│       │   │   ├── test_scanner.py      # T-B10: 스캐너
│       │   │   ├── test_news_client.py  # T-B11, T-B12: 뉴스
│       │   │   ├── test_strategy.py     # T-B13: 전략
│       │   │   ├── test_risk.py         # T-B14: 리스크
│       │   │   ├── test_order_executor.py # T-B15: 주문실행
│       │   │   ├── test_trader.py       # T-B8: 매매 루프
│       │   │   └── test_learning.py     # T-B19: 학습
│       │   │
│       │   └── models/
│       │       ├── test_db_models.py    # T-B2: ORM 모델
│       │       └── test_schemas.py      # T-B2: Pydantic 스키마
│       │
│       ├── integration/             # 통합 테스트
│       │   ├── test_api_health.py       # T-B9: health API
│       │   ├── test_api_account.py      # T-B9: account API
│       │   ├── test_api_trades.py       # T-B16: trades API
│       │   ├── test_api_strategy.py     # T-B17: strategy API
│       │   ├── test_api_reports.py      # T-B22: reports API
│       │   ├── test_websocket.py        # T-B18: WebSocket
│       │   └── test_db_operations.py    # DB CRUD 통합
│       │
│       └── e2e/                     # E2E 시나리오
│           ├── test_trade_cycle.py      # 매매 전체 사이클
│           └── test_scanner_flow.py     # 스캐너 → 전략 → 주문
│
├── frontend/
│   └── tests/
│       ├── setup.ts                 # Jest/MSW 글로벌 설정
│       │
│       ├── unit/                    # 컴포넌트 단위 테스트
│       │   ├── components/
│       │   │   ├── Dashboard.test.tsx       # T-F4
│       │   │   ├── PositionList.test.tsx    # T-F5
│       │   │   ├── TradeTable.test.tsx      # T-F7
│       │   │   ├── StrategyForm.test.tsx    # T-F8
│       │   │   ├── ScannerView.test.tsx     # T-F9
│       │   │   ├── RiskSettings.test.tsx    # T-F10
│       │   │   ├── OrderMonitor.test.tsx    # T-F11
│       │   │   └── Charts.test.tsx          # T-F12, T-F13
│       │   │
│       │   └── hooks/
│       │       ├── useAccount.test.ts       # T-F4
│       │       ├── useWebSocket.test.ts     # T-F6
│       │       └── useTrades.test.ts        # T-F7
│       │
│       ├── integration/             # API 통합 테스트
│       │   ├── api-client.test.ts       # T-F2: API 클라이언트
│       │   └── msw-handlers.test.ts     # T-F2: Mock 검증
│       │
│       └── e2e/                     # Playwright E2E
│           ├── dashboard.spec.ts        # 대시보드 플로우
│           ├── trading.spec.ts          # 매매 내역 플로우
│           └── strategy.spec.ts         # 전략 설정 플로우
```

---

# 4. Mock 전략

## 4.1 외부 API Mock (Backend)

### 키움 REST API Mock

```python
# tests/conftest.py
import respx

@pytest.fixture
def mock_kiwoom():
    with respx.mock(base_url="https://openapi.koreainvestment.com") as mock:
        # 인증
        mock.post("/oauth2/tokenP").respond(json={
            "access_token": "test-token",
            "token_type": "Bearer",
            "expires_in": 86400
        })
        # 시세 조회
        mock.get("/uapi/domestic-stock/v1/quotations/inquire-price").respond(json={
            "output": {"stck_prpr": "71000", "acml_vol": "12345678"}
        })
        yield mock
```

### StockNews API Mock

```python
@pytest.fixture
def mock_stocknews():
    with respx.mock(base_url="http://localhost:8001") as mock:
        mock.get("/api/v1/news/score").respond(json={
            "code": "005930", "score": 75, "articles": 5
        })
        yield mock
```

### Redis Mock

```python
@pytest.fixture
def fake_redis():
    return fakeredis.aioFakeRedis()
```

## 4.2 Backend API Mock (Frontend)

```typescript
// frontend/src/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/v1/account/balance', () =>
    HttpResponse.json({
      cash: 10000000,
      total_eval: 15000000,
      daily_pnl: 250000,
    })
  ),
  http.get('/api/v1/account/positions', () =>
    HttpResponse.json([
      { stock_code: '005930', stock_name: '삼성전자', quantity: 10,
        avg_price: 70000, current_price: 71000, unrealized_pnl: 10000 }
    ])
  ),
]
```

---

# 5. Phase 1 테스트 계획 (MVP)

## T-B1: 프로젝트 초기 셋업

| 항목 | 내용 |
|------|------|
| 대상 | infra (pyproject.toml, pytest 설정, Docker Compose) |
| 선행 | - |

**RED 단계:**

```python
# tests/test_setup.py
def test_pytest_runs():
    """pytest가 정상 실행되는지 확인"""
    assert True

def test_project_imports():
    """핵심 패키지 import 가능 확인"""
    import httpx
    import fastapi
    import sqlalchemy
    import redis
```

**GREEN 단계:** pyproject.toml에 의존성 설치, 디렉토리 생성

**검증:** `pytest --collect-only` 성공, `docker-compose up -d` 성공

---

## T-B2: DB 스키마 + ORM 모델

| 항목 | 내용 |
|------|------|
| 대상 | models/db_models.py, models/schemas.py |
| 선행 | T-B1 |

**RED 단계:**

```python
# tests/unit/models/test_db_models.py
def test_trade_log_model_fields():
    """trade_log 모델에 필수 필드가 존재하는지 확인"""
    from src.models.db_models import TradeLog
    columns = {c.name for c in TradeLog.__table__.columns}
    required = {'trade_id', 'date', 'stock_code', 'entry_price', 'exit_price', 'pnl', 'strategy_tag'}
    assert required.issubset(columns)

def test_learning_metrics_model_fields():
    from src.models.db_models import LearningMetrics
    columns = {c.name for c in LearningMetrics.__table__.columns}
    assert 'win_rate' in columns
    assert 'max_drawdown' in columns

def test_positions_model_fields():
    from src.models.db_models import Position
    columns = {c.name for c in Position.__table__.columns}
    assert {'stock_code', 'quantity', 'avg_price', 'stop_loss_price'}.issubset(columns)

def test_orders_model_fields():
    from src.models.db_models import Order
    columns = {c.name for c in Order.__table__.columns}
    assert {'order_id', 'side', 'status', 'filled_quantity'}.issubset(columns)

# tests/unit/models/test_schemas.py
def test_trade_log_schema_validation():
    from src.models.schemas import TradeLogResponse
    data = TradeLogResponse(trade_id="uuid", date="2026-01-01", stock_code="005930",
                           entry_price=70000, exit_price=71000, pnl=1000)
    assert data.pnl == 1000

def test_trade_log_schema_rejects_invalid():
    from src.models.schemas import TradeLogResponse
    with pytest.raises(ValidationError):
        TradeLogResponse(trade_id="uuid", date="invalid", stock_code="", entry_price=-1)
```

**GREEN 단계:** SQLAlchemy ORM 모델 4개 + Pydantic 스키마 구현

**검증 기준:**
- 4개 테이블 모델 생성 확인
- Pydantic 스키마 유효성 검사 통과
- `alembic upgrade head` 마이그레이션 성공

---

## T-B3: 키움 인증 클라이언트

| 항목 | 내용 |
|------|------|
| 대상 | kiwoom_client/auth.py |
| 선행 | T-B1 |

**RED 단계:**

```python
# tests/unit/kiwoom_client/test_auth.py
@pytest.mark.asyncio
async def test_get_token_success(mock_kiwoom):
    """정상 토큰 발급"""
    auth = KiwoomAuth(app_key="test", app_secret="test")
    token = await auth.get_token()
    assert token is not None
    assert len(token) > 0

@pytest.mark.asyncio
async def test_token_caching(mock_kiwoom):
    """토큰 캐싱: 두 번째 호출은 API 재요청 없이 캐시 반환"""
    auth = KiwoomAuth(app_key="test", app_secret="test")
    token1 = await auth.get_token()
    token2 = await auth.get_token()
    assert token1 == token2
    assert mock_kiwoom.calls.call_count == 1

@pytest.mark.asyncio
async def test_token_refresh_on_expiry(mock_kiwoom):
    """만료된 토큰 자동 갱신"""
    auth = KiwoomAuth(app_key="test", app_secret="test")
    auth._token_expires_at = datetime.now() - timedelta(seconds=1)
    token = await auth.get_token()
    assert token is not None

@pytest.mark.asyncio
async def test_token_failure_raises(mock_kiwoom):
    """인증 실패 시 예외 발생"""
    mock_kiwoom.post("/oauth2/tokenP").respond(status_code=401)
    auth = KiwoomAuth(app_key="wrong", app_secret="wrong")
    with pytest.raises(AuthenticationError):
        await auth.get_token()
```

---

## T-B4: 키움 시세 클라이언트

| 항목 | 내용 |
|------|------|
| 대상 | kiwoom_client/market.py |
| 선행 | T-B3 |

**RED 단계:**

```python
# tests/unit/kiwoom_client/test_market.py
@pytest.mark.asyncio
async def test_get_price(mock_kiwoom):
    """현재가 조회"""
    market = KiwoomMarket(auth=mock_auth)
    price = await market.get_price("005930")
    assert price["current_price"] > 0

@pytest.mark.asyncio
async def test_get_orderbook(mock_kiwoom):
    """호가 조회"""
    market = KiwoomMarket(auth=mock_auth)
    book = await market.get_orderbook("005930")
    assert "asks" in book and "bids" in book

@pytest.mark.asyncio
async def test_get_volume(mock_kiwoom):
    """거래량/거래대금 조회"""
    market = KiwoomMarket(auth=mock_auth)
    vol = await market.get_volume("005930")
    assert vol["volume"] >= 0
    assert vol["trade_value"] >= 0

@pytest.mark.asyncio
async def test_invalid_stock_code(mock_kiwoom):
    """잘못된 종목코드 에러 처리"""
    mock_kiwoom.get(path__regex=r"/inquire-price").respond(status_code=400)
    market = KiwoomMarket(auth=mock_auth)
    with pytest.raises(InvalidStockCodeError):
        await market.get_price("INVALID")
```

---

## T-B5: 키움 주문 클라이언트

| 항목 | 내용 |
|------|------|
| 대상 | kiwoom_client/order.py |
| 선행 | T-B3 |

**RED 단계:**

```python
# tests/unit/kiwoom_client/test_order.py
@pytest.mark.asyncio
async def test_buy_order(mock_kiwoom):
    """매수 주문 생성"""
    order = KiwoomOrder(auth=mock_auth)
    result = await order.buy("005930", qty=10, price=70000)
    assert result["order_id"] is not None
    assert result["status"] == "submitted"

@pytest.mark.asyncio
async def test_sell_order(mock_kiwoom):
    """매도 주문 생성"""
    order = KiwoomOrder(auth=mock_auth)
    result = await order.sell("005930", qty=10, price=71000)
    assert result["status"] == "submitted"

@pytest.mark.asyncio
async def test_cancel_order(mock_kiwoom):
    """주문 취소"""
    order = KiwoomOrder(auth=mock_auth)
    result = await order.cancel(order_id="ORD001")
    assert result["status"] == "cancelled"

@pytest.mark.asyncio
async def test_order_status_query(mock_kiwoom):
    """체결 상태 조회"""
    order = KiwoomOrder(auth=mock_auth)
    status = await order.get_status(order_id="ORD001")
    assert status["status"] in ("pending", "filled", "cancelled", "failed")

@pytest.mark.asyncio
async def test_order_zero_quantity_rejected():
    """수량 0 주문 거부"""
    order = KiwoomOrder(auth=mock_auth)
    with pytest.raises(ValueError):
        await order.buy("005930", qty=0, price=70000)
```

---

## T-B6: 키움 계좌 클라이언트

| 항목 | 내용 |
|------|------|
| 대상 | kiwoom_client/account.py |
| 선행 | T-B3 |

**RED 단계:**

```python
# tests/unit/kiwoom_client/test_account.py
@pytest.mark.asyncio
async def test_get_balance(mock_kiwoom):
    """예수금 조회"""
    account = KiwoomAccount(auth=mock_auth)
    balance = await account.get_balance()
    assert "cash" in balance
    assert balance["cash"] >= 0

@pytest.mark.asyncio
async def test_get_positions(mock_kiwoom):
    """보유종목 리스트"""
    account = KiwoomAccount(auth=mock_auth)
    positions = await account.get_positions()
    assert isinstance(positions, list)

@pytest.mark.asyncio
async def test_get_pnl(mock_kiwoom):
    """평가손익 조회"""
    account = KiwoomAccount(auth=mock_auth)
    pnl = await account.get_pnl()
    assert "total_eval" in pnl
    assert "unrealized_pnl" in pnl
```

---

## T-B7: Market Data Collector

| 항목 | 내용 |
|------|------|
| 대상 | core/market_data.py |
| 선행 | T-B4 |

**RED 단계:**

```python
# tests/unit/core/test_market_data.py
@pytest.mark.asyncio
async def test_collect_prices(mock_kiwoom):
    """시세 수집 동작 확인"""
    collector = MarketDataCollector(market_client=mock_market)
    data = await collector.collect(["005930", "000660"])
    assert len(data) == 2
    assert data["005930"]["price"] > 0

def test_calculate_trade_value():
    """거래대금 계산"""
    collector = MarketDataCollector(market_client=mock_market)
    value = collector.calc_trade_value(price=70000, volume=1000)
    assert value == 70_000_000

def test_calculate_vwap():
    """VWAP 계산"""
    trades = [
        {"price": 70000, "volume": 100},
        {"price": 71000, "volume": 200},
    ]
    vwap = MarketDataCollector.calc_vwap(trades)
    expected = (70000*100 + 71000*200) / 300
    assert abs(vwap - expected) < 0.01

def test_aggregate_1min_candle():
    """1분봉 집계"""
    ticks = [
        {"time": "09:00:01", "price": 70000},
        {"time": "09:00:30", "price": 70500},
        {"time": "09:00:59", "price": 70200},
    ]
    candle = MarketDataCollector.aggregate_candle(ticks, interval="1m")
    assert candle["open"] == 70000
    assert candle["high"] == 70500
    assert candle["low"] == 70000
    assert candle["close"] == 70200
```

---

## T-B8: 기본 자동매매 루프

| 항목 | 내용 |
|------|------|
| 대상 | core/trader.py |
| 선행 | T-B5, T-B7 |

**RED 단계:**

```python
# tests/unit/core/test_trader.py
@pytest.mark.asyncio
async def test_trader_starts_and_stops():
    """매매 루프 시작/정지"""
    trader = Trader(config=test_config)
    await trader.start()
    assert trader.is_running is True
    await trader.stop()
    assert trader.is_running is False

@pytest.mark.asyncio
async def test_trader_executes_cycle(mock_kiwoom):
    """매매 사이클 1회 실행"""
    trader = Trader(config=test_config)
    result = await trader.run_cycle()
    assert result["status"] in ("executed", "no_signal", "skipped")

@pytest.mark.asyncio
async def test_trader_respects_market_hours():
    """장 외 시간에는 매매하지 않음"""
    trader = Trader(config=test_config)
    trader._now = lambda: datetime(2026, 1, 1, 7, 0)  # 장 전
    result = await trader.run_cycle()
    assert result["status"] == "market_closed"
```

---

## T-B9: FastAPI 기본 API

| 항목 | 내용 |
|------|------|
| 대상 | api/ (health, account, positions) |
| 선행 | T-B2 |

**RED 단계:**

```python
# tests/integration/test_api_health.py
@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    assert "status" in resp.json()

# tests/integration/test_api_account.py
@pytest.mark.asyncio
async def test_get_balance(async_client, mock_kiwoom):
    resp = await async_client.get("/api/v1/account/balance")
    assert resp.status_code == 200
    data = resp.json()
    assert "cash" in data

@pytest.mark.asyncio
async def test_get_positions(async_client, mock_kiwoom):
    resp = await async_client.get("/api/v1/account/positions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

---

## T-F1 ~ T-F6: Frontend Phase 1 테스트

### T-F1: 프로젝트 초기 셋업

```typescript
// tests/setup.test.ts
test('React app renders without crash', () => {
  render(<App />)
  expect(document.body).toBeTruthy()
})
```

### T-F2: API 클라이언트 + Mock

```typescript
// tests/integration/api-client.test.ts
test('fetchBalance returns account data', async () => {
  const data = await apiClient.getBalance()
  expect(data).toHaveProperty('cash')
  expect(data).toHaveProperty('total_eval')
})

test('API client handles 500 error gracefully', async () => {
  server.use(http.get('/api/v1/account/balance', () =>
    HttpResponse.json({ error: 'Internal' }, { status: 500 })
  ))
  await expect(apiClient.getBalance()).rejects.toThrow()
})
```

### T-F3: 인증 UI

```typescript
// tests/unit/components/AuthSettings.test.tsx
test('API key input renders', () => {
  render(<AuthSettings />)
  expect(screen.getByLabelText(/API Key/i)).toBeInTheDocument()
})

test('saves API key on submit', async () => {
  render(<AuthSettings />)
  await userEvent.type(screen.getByLabelText(/API Key/i), 'test-key')
  await userEvent.click(screen.getByRole('button', { name: /저장/i }))
  expect(screen.getByText(/저장 완료/i)).toBeInTheDocument()
})
```

### T-F4: 계좌 대시보드

```typescript
// tests/unit/components/Dashboard.test.tsx
test('displays account balance', async () => {
  render(<Dashboard />)
  await waitFor(() => {
    expect(screen.getByText(/예수금/)).toBeInTheDocument()
    expect(screen.getByText(/10,000,000/)).toBeInTheDocument()
  })
})

test('displays daily PnL with color', async () => {
  render(<Dashboard />)
  await waitFor(() => {
    const pnl = screen.getByTestId('daily-pnl')
    expect(pnl).toHaveClass('text-green')  // 양수 = 녹색
  })
})
```

### T-F5: 포지션 현황

```typescript
// tests/unit/components/PositionList.test.tsx
test('renders position list', async () => {
  render(<PositionList />)
  await waitFor(() => {
    expect(screen.getByText('삼성전자')).toBeInTheDocument()
  })
})

test('shows empty state when no positions', async () => {
  server.use(http.get('/api/v1/account/positions', () =>
    HttpResponse.json([])
  ))
  render(<PositionList />)
  await waitFor(() => {
    expect(screen.getByText(/보유 종목 없음/)).toBeInTheDocument()
  })
})
```

### T-F6: 실시간 상태 (WebSocket)

```typescript
// tests/unit/hooks/useWebSocket.test.ts
test('connects to WebSocket and receives updates', async () => {
  const wsServer = new WS('ws://localhost:8000/ws/live')
  const { result } = renderHook(() => useWebSocket())

  wsServer.send(JSON.stringify({
    type: 'system_status',
    data: { status: 'running', active_positions: 3 }
  }))

  await waitFor(() => {
    expect(result.current.systemStatus).toBe('running')
  })
})
```

---

# 6. Phase 2 테스트 계획 (전략 연동)

## T-B10: Opening Scanner

| 항목 | 내용 |
|------|------|
| 대상 | core/scanner.py |
| 선행 | T-B7 |

**RED 단계:**

```python
# tests/unit/core/test_scanner.py
def test_rank_by_trade_value():
    """거래대금 랭킹"""
    stocks = [
        {"code": "005930", "trade_value": 500_000_000},
        {"code": "000660", "trade_value": 800_000_000},
        {"code": "035720", "trade_value": 300_000_000},
    ]
    ranked = Scanner.rank_by_trade_value(stocks, top_n=2)
    assert len(ranked) == 2
    assert ranked[0]["code"] == "000660"

def test_detect_volume_surge():
    """전일 대비 거래량 급증 감지"""
    result = Scanner.detect_volume_surge(
        today_volume=1_000_000, prev_volume=200_000, threshold=3.0
    )
    assert result is True

def test_calculate_opening_range():
    """장초 Range 계산 (09:00~09:30 고/저)"""
    candles = [
        {"time": "09:00", "high": 71000, "low": 69500},
        {"time": "09:15", "high": 71500, "low": 70000},
        {"time": "09:30", "high": 72000, "low": 70500},
    ]
    range_ = Scanner.calc_opening_range(candles)
    assert range_["high"] == 72000
    assert range_["low"] == 69500
```

---

## T-B11: StockNews REST 연동

```python
# tests/unit/core/test_news_client.py
@pytest.mark.asyncio
async def test_get_news_score(mock_stocknews):
    """뉴스 점수 조회"""
    client = NewsClient(base_url="http://localhost:8001")
    score = await client.get_score("005930")
    assert 0 <= score <= 100

@pytest.mark.asyncio
async def test_news_score_caching(mock_stocknews):
    """점수 캐싱: TTL 내 재요청 없음"""
    client = NewsClient(base_url="http://localhost:8001", cache_ttl=60)
    score1 = await client.get_score("005930")
    score2 = await client.get_score("005930")
    assert score1 == score2
    # API는 1번만 호출되어야 함

@pytest.mark.asyncio
async def test_news_service_unavailable(mock_stocknews):
    """뉴스 서비스 다운 시 기본값 반환"""
    mock_stocknews.get(path__regex=r"/news/score").respond(status_code=503)
    client = NewsClient(base_url="http://localhost:8001")
    score = await client.get_score("005930")
    assert score == 0  # 기본값
```

---

## T-B12: Redis 뉴스 구독

```python
# tests/unit/core/test_news_client.py (추가)
@pytest.mark.asyncio
async def test_redis_subscribe(fake_redis):
    """Redis 채널 구독 및 메시지 수신"""
    client = NewsClient(redis=fake_redis)
    received = []
    client.on_breaking_news(lambda msg: received.append(msg))
    await client.subscribe("news_breaking_kr")

    await fake_redis.publish("news_breaking_kr", json.dumps({
        "code": "005930", "headline": "삼성전자 실적 발표", "score": 85
    }))

    assert len(received) == 1
    assert received[0]["score"] == 85
```

---

## T-B13: Strategy Engine

```python
# tests/unit/core/test_strategy.py
def test_buy_signal_all_conditions_met():
    """모든 매수 조건 충족 → 매수 신호"""
    strategy = Strategy(config=test_strategy_config)
    signal = strategy.evaluate(
        volume_rank=3, news_score=75,
        current_price=71000, opening_high=70500, vwap=70800
    )
    assert signal.action == "buy"

def test_no_signal_low_news_score():
    """뉴스 점수 미달 → 신호 없음"""
    strategy = Strategy(config=test_strategy_config)
    signal = strategy.evaluate(
        volume_rank=3, news_score=30,
        current_price=71000, opening_high=70500, vwap=70800
    )
    assert signal.action == "hold"

def test_no_signal_below_vwap():
    """VWAP 하회 → 신호 없음"""
    strategy = Strategy(config=test_strategy_config)
    signal = strategy.evaluate(
        volume_rank=3, news_score=75,
        current_price=69000, opening_high=70500, vwap=70800
    )
    assert signal.action == "hold"

def test_config_from_yaml():
    """YAML 파일로 전략 파라미터 로드"""
    strategy = Strategy.from_yaml("tests/fixtures/strategy_config.yaml")
    assert strategy.config.top_n == 5
    assert strategy.config.news_threshold == 70
```

---

## T-B14: Risk Management

```python
# tests/unit/core/test_risk.py
def test_position_size_within_limit():
    """종목당 비중 10% 이하"""
    risk = RiskManager(max_position_pct=0.10, total_capital=10_000_000)
    size = risk.calc_position_size(price=70000)
    assert size * 70000 <= 1_000_000

def test_stop_loss_triggered():
    """손절 가격 도달 시 청산 신호"""
    risk = RiskManager(stop_loss_pct=0.03)
    signal = risk.check_stop_loss(entry_price=70000, current_price=67800)
    assert signal == "sell"

def test_daily_loss_limit():
    """1일 최대 손실 초과 시 매매 중단"""
    risk = RiskManager(daily_loss_limit=500_000)
    risk.record_loss(300_000)
    assert risk.can_trade() is True
    risk.record_loss(250_000)
    assert risk.can_trade() is False

def test_max_concurrent_positions():
    """동시 보유 종목 수 제한"""
    risk = RiskManager(max_positions=5)
    risk.current_positions = 5
    assert risk.can_open_position() is False

def test_emergency_liquidation():
    """비상 전체 청산"""
    risk = RiskManager()
    signals = risk.emergency_liquidate(positions=[
        {"code": "005930", "qty": 10},
        {"code": "000660", "qty": 5},
    ])
    assert len(signals) == 2
    assert all(s["action"] == "sell_all" for s in signals)
```

---

## T-B15: Order Execution 고도화

```python
# tests/unit/core/test_order_executor.py
@pytest.mark.asyncio
async def test_split_order():
    """분할 매수 (총 100주를 20주씩)"""
    executor = OrderExecutor(order_client=mock_order, split_size=20)
    results = await executor.execute_split_buy("005930", qty=100, price=70000)
    assert len(results) == 5

@pytest.mark.asyncio
async def test_retry_on_failure(mock_kiwoom):
    """주문 실패 시 재시도"""
    mock_kiwoom.post(path__regex=r"/order").mock(side_effect=[
        httpx.Response(500), httpx.Response(200, json={"order_id": "ORD001"})
    ])
    executor = OrderExecutor(order_client=mock_order, max_retries=3)
    result = await executor.execute_buy("005930", qty=10, price=70000)
    assert result["order_id"] == "ORD001"

@pytest.mark.asyncio
async def test_slippage_protection():
    """슬리피지 한도 초과 시 주문 취소"""
    executor = OrderExecutor(max_slippage_pct=0.005)
    result = await executor.execute_buy("005930", qty=10, price=70000, market_price=70500)
    assert result["status"] == "cancelled_slippage"
```

---

## T-B16 ~ T-B18: API 확장 + WebSocket

### T-B16: 매매 내역 API

```python
# tests/integration/test_api_trades.py
@pytest.mark.asyncio
async def test_get_trades_with_pagination(async_client, seed_trades):
    resp = await async_client.get("/api/v1/trades?page=1&size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 10
    assert "total" in data

@pytest.mark.asyncio
async def test_get_trades_filter_by_date(async_client, seed_trades):
    resp = await async_client.get("/api/v1/trades?date_from=2026-01-01&date_to=2026-01-31")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_get_trade_detail(async_client, seed_trades):
    resp = await async_client.get(f"/api/v1/trades/{seed_trades[0].trade_id}")
    assert resp.status_code == 200
    assert resp.json()["trade_id"] is not None
```

### T-B17: 전략 관리 API

```python
# tests/integration/test_api_strategy.py
@pytest.mark.asyncio
async def test_get_strategy_config(async_client):
    resp = await async_client.get("/api/v1/strategy/config")
    assert resp.status_code == 200
    assert "top_n" in resp.json()

@pytest.mark.asyncio
async def test_update_strategy_config(async_client):
    resp = await async_client.put("/api/v1/strategy/config",
        json={"top_n": 10, "news_threshold": 60})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_toggle_strategy(async_client):
    resp = await async_client.post("/api/v1/strategy/toggle",
        json={"enabled": False})
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
```

### T-B18: WebSocket 실시간

```python
# tests/integration/test_websocket.py
@pytest.mark.asyncio
async def test_websocket_connection(async_client):
    async with async_client.websocket_connect("/ws/live") as ws:
        data = await ws.receive_json()
        assert data["type"] in ("system_status", "price_update")

@pytest.mark.asyncio
async def test_websocket_receives_trade_signal(async_client):
    async with async_client.websocket_connect("/ws/live") as ws:
        # 매매 신호 트리거 후 WebSocket으로 수신 확인
        data = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
        assert "type" in data
```

---

## T-F7 ~ T-F11: Frontend Phase 2 테스트

### T-F7: 매매 내역 페이지

```typescript
test('renders trade table with data', async () => {
  render(<TradesPage />)
  await waitFor(() => {
    expect(screen.getByText('005930')).toBeInTheDocument()
  })
})

test('filters trades by date range', async () => {
  render(<TradesPage />)
  await userEvent.type(screen.getByLabelText(/시작일/), '2026-01-01')
  await userEvent.click(screen.getByRole('button', { name: /검색/ }))
  await waitFor(() => {
    expect(screen.getAllByRole('row').length).toBeGreaterThan(1)
  })
})

test('paginates trade results', async () => {
  render(<TradesPage />)
  await waitFor(() => {
    expect(screen.getByText(/다음/)).toBeInTheDocument()
  })
})
```

### T-F8: 전략 설정 페이지

```typescript
test('renders strategy form with current values', async () => {
  render(<StrategyPage />)
  await waitFor(() => {
    expect(screen.getByLabelText(/TOP N/)).toHaveValue('5')
  })
})

test('updates strategy parameters', async () => {
  render(<StrategyPage />)
  await userEvent.clear(screen.getByLabelText(/TOP N/))
  await userEvent.type(screen.getByLabelText(/TOP N/), '10')
  await userEvent.click(screen.getByRole('button', { name: /저장/ }))
  await waitFor(() => {
    expect(screen.getByText(/저장 완료/)).toBeInTheDocument()
  })
})
```

### T-F9: 장초 스캐너 뷰

```typescript
test('displays real-time top N stocks', async () => {
  render(<ScannerPage />)
  await waitFor(() => {
    expect(screen.getByText(/거래대금 TOP/)).toBeInTheDocument()
  })
})
```

### T-F10: 리스크 설정 UI

```typescript
test('renders risk settings form', async () => {
  render(<RiskSettingsPage />)
  expect(screen.getByLabelText(/손절률/)).toBeInTheDocument()
  expect(screen.getByLabelText(/최대 비중/)).toBeInTheDocument()
})

test('emergency sell button requires confirmation', async () => {
  render(<RiskSettingsPage />)
  await userEvent.click(screen.getByRole('button', { name: /비상 청산/ }))
  expect(screen.getByText(/정말 전체 청산/)).toBeInTheDocument()
})
```

### T-F11: 주문 모니터링

```typescript
test('displays real-time order updates via WebSocket', async () => {
  const wsServer = new WS('ws://localhost:8000/ws/live')
  render(<OrderMonitor />)

  wsServer.send(JSON.stringify({
    type: 'order_filled',
    data: { order_id: 'ORD001', code: '005930', price: 71000 }
  }))

  await waitFor(() => {
    expect(screen.getByText('체결')).toBeInTheDocument()
  })
})
```

---

# 7. Phase 3 테스트 계획 (고도화)

## T-B19: Learning DB

```python
# tests/unit/core/test_learning.py
def test_calculate_win_rate():
    trades = [{"pnl": 1000}, {"pnl": -500}, {"pnl": 2000}]
    result = LearningAnalyzer.calc_win_rate(trades)
    assert abs(result - 66.67) < 0.1

def test_calculate_max_drawdown():
    equity_curve = [100, 110, 95, 105, 90, 100]
    mdd = LearningAnalyzer.calc_max_drawdown(equity_curve)
    assert abs(mdd - 18.18) < 0.1  # (110→90)/110

def test_identify_best_worst_pattern():
    trades = [
        {"strategy_tag": "volume_leader", "pnl": 5000},
        {"strategy_tag": "news_breakout", "pnl": -3000},
        {"strategy_tag": "volume_leader", "pnl": 3000},
    ]
    patterns = LearningAnalyzer.identify_patterns(trades)
    assert patterns["best"] == "volume_leader"
    assert patterns["worst"] == "news_breakout"
```

## T-B20 ~ T-B22: 리포트 + 통계 API

```python
# tests/unit/core/test_report.py
def test_generate_daily_report(seed_trades):
    report = ReportGenerator.daily(date="2026-01-15", trades=seed_trades)
    assert report["total_trades"] > 0
    assert "win_rate" in report
    assert "total_pnl" in report

# tests/integration/test_api_reports.py
@pytest.mark.asyncio
async def test_get_daily_report(async_client, seed_learning_metrics):
    resp = await async_client.get("/api/v1/reports/daily?date=2026-01-15")
    assert resp.status_code == 200
    assert "win_rate" in resp.json()

@pytest.mark.asyncio
async def test_get_metrics(async_client, seed_learning_metrics):
    resp = await async_client.get("/api/v1/reports/metrics")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

## T-F12 ~ T-F14: Frontend Phase 3 테스트

```typescript
// T-F12: 성과 분석 차트
test('renders profit chart with data', async () => {
  render(<ProfitChart />)
  await waitFor(() => {
    expect(screen.getByTestId('profit-chart')).toBeInTheDocument()
  })
})

// T-F13: 학습 메트릭
test('displays drawdown visualization', async () => {
  render(<MetricsDashboard />)
  await waitFor(() => {
    expect(screen.getByText(/Max Drawdown/)).toBeInTheDocument()
  })
})

// T-F14: 리포트 뷰어
test('loads and displays daily report', async () => {
  render(<ReportViewer />)
  await userEvent.selectOptions(screen.getByLabelText(/날짜/), '2026-01-15')
  await waitFor(() => {
    expect(screen.getByText(/승률/)).toBeInTheDocument()
  })
})
```

---

# 8. E2E 테스트 시나리오

## 8.1 Backend E2E: 매매 전체 사이클

```python
# tests/e2e/test_trade_cycle.py
@pytest.mark.asyncio
async def test_full_trade_cycle(mock_kiwoom, mock_stocknews, test_db):
    """
    시세수집 → 스캐너 → 뉴스점수 → 전략판단 → 리스크확인 → 주문 → 체결 → DB 기록
    """
    trader = Trader(config=e2e_config)
    await trader.run_cycle()

    # DB에 주문 기록 확인
    orders = await test_db.query(Order).all()
    assert len(orders) >= 1

    # trade_log에 기록 확인
    trades = await test_db.query(TradeLog).all()
    assert len(trades) >= 1
```

## 8.2 Frontend E2E: Playwright

```typescript
// tests/e2e/dashboard.spec.ts
test('full dashboard flow', async ({ page }) => {
  await page.goto('http://localhost:3000')

  // 대시보드 로드 확인
  await expect(page.getByText('예수금')).toBeVisible()
  await expect(page.getByText('포지션')).toBeVisible()

  // 매매 내역 이동
  await page.click('text=매매 내역')
  await expect(page.url()).toContain('/trades')

  // 전략 설정 이동
  await page.click('text=전략 설정')
  await expect(page.getByLabel('TOP N')).toBeVisible()
})
```

---

# 9. CI/CD 테스트 파이프라인

```yaml
# .github/workflows/test.yml
name: StockAgent Tests

on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: stockagent_test
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: cd backend && pip install -e ".[dev]"
      - run: cd backend && pytest --cov=src --cov-report=xml -v
      - name: Coverage Gate
        run: |
          coverage=$(python -c "import xml.etree.ElementTree as ET; print(float(ET.parse('backend/coverage.xml').getroot().attrib['line-rate'])*100)")
          echo "Coverage: $coverage%"
          python -c "assert $coverage >= 80, f'Coverage {$coverage}% < 80%'"

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm test -- --coverage --watchAll=false
      - name: Coverage Gate
        run: cd frontend && npx jest --coverage --coverageThreshold='{"global":{"lines":70}}'

  e2e-test:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker-compose up -d
      - run: cd frontend && npx playwright install && npx playwright test
```

---

# 10. 커버리지 목표 및 품질 게이트

| 계층 | 목표 | 필수 항목 |
|------|------|-----------|
| Backend Unit | 80%+ | 모든 public 함수 |
| Backend Integration | API 전 엔드포인트 | 200/400/500 응답 |
| Frontend Unit | 70%+ | 모든 컴포넌트 렌더링 |
| Frontend E2E | 핵심 플로우 3개 | 대시보드, 매매, 전략 |

### 품질 게이트 (PR 머지 조건)

* pytest 전체 통과
* jest 전체 통과
* Backend 커버리지 80% 이상
* Frontend 커버리지 70% 이상
* E2E 테스트 통과 (Phase 2+)
* 새 public 함수에 테스트 필수

---

# 11. TestAgent 실행 가이드

## 11.1 개발 태스크별 TDD 절차

각 태스크(B-n 또는 F-n) 시작 시:

```
1. 이 문서에서 해당 T-B{n} 또는 T-F{n} 섹션 참조
2. RED:  테스트 코드를 먼저 작성 → pytest / jest 실행 → 실패 확인
3. GREEN: 최소 구현 코드 작성 → 테스트 통과 확인
4. REFACTOR: 코드 정리 → 테스트 재실행 → 여전히 통과 확인
5. 커버리지 확인 → 80%/70% 미달 시 테스트 추가
```

## 11.2 테스트 실행 명령

```bash
# Backend 전체 테스트
cd backend && pytest -v --cov=src --cov-report=term-missing

# Backend 특정 모듈
cd backend && pytest tests/unit/kiwoom_client/test_auth.py -v

# Frontend 전체 테스트
cd frontend && npm test -- --watchAll=false --coverage

# Frontend 특정 파일
cd frontend && npm test -- Dashboard.test.tsx

# E2E 테스트
cd frontend && npx playwright test

# 커버리지 리포트 생성
cd backend && pytest --cov=src --cov-report=html
open backend/htmlcov/index.html
```

## 11.3 태스크 ID 매핑 요약

| 테스트 ID | 개발 태스크 | 테스트 유형 | 테스트 파일 |
|-----------|------------|------------|------------|
| T-B1 | B-1 셋업 | Unit | test_setup.py |
| T-B2 | B-2 DB 모델 | Unit | test_db_models.py, test_schemas.py |
| T-B3 | B-3 키움 인증 | Unit | test_auth.py |
| T-B4 | B-4 키움 시세 | Unit | test_market.py |
| T-B5 | B-5 키움 주문 | Unit | test_order.py |
| T-B6 | B-6 키움 계좌 | Unit | test_account.py |
| T-B7 | B-7 시세 수집 | Unit | test_market_data.py |
| T-B8 | B-8 매매 루프 | Unit | test_trader.py |
| T-B9 | B-9 기본 API | Integration | test_api_health.py, test_api_account.py |
| T-B10 | B-10 스캐너 | Unit | test_scanner.py |
| T-B11 | B-11 뉴스 REST | Unit | test_news_client.py |
| T-B12 | B-12 뉴스 Redis | Unit | test_news_client.py |
| T-B13 | B-13 전략 엔진 | Unit | test_strategy.py |
| T-B14 | B-14 리스크 | Unit | test_risk.py |
| T-B15 | B-15 주문 실행 | Unit | test_order_executor.py |
| T-B16 | B-16 매매 API | Integration | test_api_trades.py |
| T-B17 | B-17 전략 API | Integration | test_api_strategy.py |
| T-B18 | B-18 WebSocket | Integration | test_websocket.py |
| T-B19 | B-19 학습 DB | Unit | test_learning.py |
| T-B20 | B-20 리포트 | Unit | test_report.py |
| T-B21 | B-21 튜닝 | Unit | test_tuner.py |
| T-B22 | B-22 리포트 API | Integration | test_api_reports.py |
| T-F1 | F-1 셋업 | Unit | setup.test.ts |
| T-F2 | F-2 API Mock | Integration | api-client.test.ts |
| T-F3 | F-3 인증 UI | Unit | AuthSettings.test.tsx |
| T-F4 | F-4 대시보드 | Unit | Dashboard.test.tsx |
| T-F5 | F-5 포지션 | Unit | PositionList.test.tsx |
| T-F6 | F-6 실시간 | Unit | useWebSocket.test.ts |
| T-F7 | F-7 매매 내역 | Unit | TradeTable.test.tsx |
| T-F8 | F-8 전략 설정 | Unit | StrategyForm.test.tsx |
| T-F9 | F-9 스캐너 뷰 | Unit | ScannerView.test.tsx |
| T-F10 | F-10 리스크 | Unit | RiskSettings.test.tsx |
| T-F11 | F-11 주문 모니터 | Unit | OrderMonitor.test.tsx |
| T-F12 | F-12 분석 차트 | Unit | Charts.test.tsx |
| T-F13 | F-13 학습 메트릭 | Unit | Charts.test.tsx |
| T-F14 | F-14 리포트 뷰어 | Unit | ReportViewer.test.tsx |
