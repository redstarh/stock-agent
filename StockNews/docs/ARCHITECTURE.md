# StockNews System Architecture

**문서 버전:** 1.0
**작성일:** 2026-02-21
**상태:** Production (Phase 1-3 완료)

---

## 목차

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Data Architecture](#3-data-architecture)
4. [API Architecture](#4-api-architecture)
5. [ML Pipeline Architecture](#5-ml-pipeline-architecture)
6. [Deployment Architecture](#6-deployment-architecture)
7. [Security Architecture](#7-security-architecture)
8. [Integration Architecture](#8-integration-architecture)

---

## 1. System Overview

### 1.1 High-Level Architecture

StockNews는 한국/미국 주식 시장의 뉴스를 수집, 분석, 점수화하여 자동매매 시스템(StockAgent)에 인텔리전스를 제공하는 독립 서비스입니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                    External News Sources                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Naver   │  │   DART   │  │ Finnhub  │  │   NewsAPI    │  │
│  │  Finance │  │   Open   │  │   News   │  │   Global     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
└───────┼─────────────┼─────────────┼────────────────┼──────────┘
        │             │             │                │
        └─────────────┴─────────────┴────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Collection Layer (APScheduler)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ KR Collector │  │ DART         │  │ US Collector         │ │
│  │ (1분 주기)   │  │ Collector    │  │ (3분 주기)           │ │
│  │              │  │ (5분 주기)   │  │                      │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────────┘ │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Dedup       │→│ Stock       │→│ Sentiment/Theme    │   │
│  │ (URL/Title) │  │ Mapper      │  │ Classifier (LLM)   │   │
│  └─────────────┘  └─────────────┘  └──────────┬──────────┘   │
└────────────────────────────────────────────────┼──────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Scoring Engine                               │
│  Score = Recency×0.4 + Frequency×0.3 + Sentiment×0.2           │
│          + Disclosure×0.1                                       │
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │ Theme          │  │ Stock          │  │ Prediction      │ │
│  │ Aggregator     │  │ Aggregator     │  │ Model (RF)      │ │
│  └────────────────┘  └────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer (PostgreSQL + Redis)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐│
│  │ news_event   │  │ theme_       │  │ prediction_          ││
│  │ (192 tests)  │  │ strength     │  │ result               ││
│  └──────────────┘  └──────────────┘  └──────────────────────┘│
│                                                                 │
│  Redis Cache + Pub/Sub (breaking_news channel)                 │
└─────────────────────────────────────────────────────────────────┘
          │                                      │
          ▼                                      ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│   REST API + WebSocket   │    │   Redis Pub/Sub              │
│   (FastAPI)              │    │   (breaking_news)            │
│   - /api/v1/news/*       │    │   score >= 80 threshold      │
│   - /api/v1/stocks/*     │    │                              │
│   - /api/v1/themes/*     │    │                              │
│   - /api/v1/prediction/* │    │                              │
│   - /ws/news             │    │                              │
└─────────┬────────────────┘    └──────────┬───────────────────┘
          │                                 │
          ▼                                 ▼
┌─────────────────────────┐    ┌───────────────────────────────┐
│   Frontend (React)      │    │   StockAgent (Consumer)       │
│   - Dashboard           │    │   - Buy Signal Decision       │
│   - Stock Detail        │    │   - Breaking News Alert       │
│   - Theme Analysis      │    │                               │
│   - Prediction View     │    │                               │
│   - Verification View   │    │                               │
└─────────────────────────┘    └───────────────────────────────┘
```

### 1.2 Component Relationships

**독립성 (Loose Coupling):**
- StockNews는 StockAgent에 의존하지 않음 (Provider 역할)
- 단방향 데이터 흐름: StockNews → StockAgent
- StockAgent 장애가 StockNews에 영향 없음

**데이터 흐름:**
1. **수집 (Collection):** 외부 소스 → Collectors → Raw Items
2. **처리 (Processing):** Raw Items → Pipeline → Structured NewsEvent
3. **분석 (Analysis):** NewsEvent → LLM → Sentiment + Theme
4. **점수화 (Scoring):** NewsEvent → Engine → News Score
5. **집계 (Aggregation):** News Score → Aggregators → Theme/Stock Metrics
6. **예측 (Prediction):** Features → ML Model → Prediction Result
7. **제공 (Serving):** API/WebSocket/Pub-Sub → Consumers

---

## 2. Technology Stack

### 2.1 Backend Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.12+ (dev: 3.13) | 서버 개발 |
| **Web Framework** | FastAPI | 0.109+ | REST API + WebSocket |
| **ASGI Server** | Uvicorn | 0.27+ | Production server |
| **ORM** | SQLAlchemy | 2.0.25+ | Database abstraction (sync) |
| **DB (Dev)** | SQLite + aiosqlite | - | Local development |
| **DB (Prod)** | PostgreSQL | 15+ | Production database |
| **Migration** | Alembic | 1.13+ | Schema versioning |
| **Cache/Pub-Sub** | Redis | 7+ | Caching + event streaming |
| **Scheduler** | APScheduler | 3.10+ | Periodic collection jobs |
| **HTTP Client** | httpx | 0.26+ | Async HTTP requests |
| **Validation** | Pydantic | 2.5+ | Schema validation |
| **Config** | pydantic-settings | 2.1+ | Environment management |
| **NLP/LLM** | OpenAI API | 1.10+ | Sentiment + summarization |
| **NLP/LLM (Alt)** | AWS Bedrock | boto3 1.34+ | Claude via Bedrock |
| **ML** | scikit-learn | 1.3+ | Random Forest prediction |
| **Data** | pandas | 2.0+ | Data manipulation |
| **Stock Prices** | yfinance | 1.2+ | Historical price data |
| **Logging** | structlog | 24.1+ | Structured logging |
| **Monitoring** | Sentry | 1.40+ | Error tracking |
| **Metrics** | prometheus-fastapi-instrumentator | 6.1+ | Prometheus metrics |
| **Rate Limiting** | slowapi | 0.1.9+ | API rate limiting |
| **Secrets** | boto3 (AWS Secrets Manager) | 1.34+ | Secret management |

**Dependencies (pyproject.toml):**
```toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",      # PostgreSQL async driver
    "aiosqlite>=0.19.0",     # SQLite async driver
    "redis>=5.0.0",
    "apscheduler>=3.10.4",
    "httpx>=0.26.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "structlog>=24.1.0",
    "beautifulsoup4>=4.12.0",
    "feedparser>=6.0.0",
    "openai>=1.10.0",
    "boto3>=1.34.0",
    "scikit-learn>=1.3.0",
    "slowapi>=0.1.9",
    "yfinance>=1.2.0",
    "pandas>=2.0.0",
    "joblib>=1.3.0",
    "psycopg2-binary>=2.9.0",
    "sentry-sdk[fastapi]>=1.40.0",
    "prometheus-fastapi-instrumentator>=6.1.0",
]
```

### 2.2 Frontend Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | TypeScript | 5.9+ | Type-safe development |
| **UI Framework** | React | 19.2 | Component-based UI |
| **Build Tool** | Vite | 7.3+ | Fast build + HMR |
| **Server State** | TanStack Query | 5.90+ | API data caching/sync |
| **Charts** | Recharts | 3.7+ | Data visualization |
| **Styling** | Tailwind CSS | 4.1+ | Utility-first CSS |
| **Routing** | React Router | 7.13+ | SPA routing |
| **HTTP Client** | Axios | 1.13+ | API requests |
| **Testing (Unit)** | Vitest | 4.0+ | Unit/integration tests |
| **Testing (E2E)** | Playwright | 1.58+ | End-to-end tests |
| **Mocking** | MSW | 2.12+ | API mocking |
| **Linter** | ESLint | 9.39+ | Code quality |
| **Formatter** | Prettier | 3.8+ | Code formatting |

**Dependencies (package.json):**
```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.90.21",
    "axios": "^1.13.5",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router-dom": "^7.13.0",
    "recharts": "^3.7.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.58.2",
    "@tailwindcss/vite": "^4.1.18",
    "@testing-library/react": "^16.3.2",
    "@vitejs/plugin-react": "^5.1.1",
    "@vitest/coverage-v8": "^4.0.18",
    "eslint": "^9.39.2",
    "msw": "^2.12.10",
    "prettier": "^3.8.1",
    "typescript": "~5.9.3",
    "vite": "^7.3.1",
    "vitest": "^4.0.18"
  }
}
```

### 2.3 Infrastructure Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Container** | Docker | Containerization |
| **Orchestration** | Docker Compose | Local dev environment |
| **CI/CD** | GitHub Actions | Automated testing + deployment |
| **Version Control** | Git | Source code management |
| **Linter (Python)** | Ruff | Fast Python linting |
| **Type Checker** | mypy (optional) | Static type checking |

### 2.4 External APIs

| API | Purpose | Market | Rate Limit |
|-----|---------|--------|------------|
| **Naver Finance** | 한국 뉴스 크롤링 | KR | Scraping (조심스럽게) |
| **DART Open API** | 한국 공시 정보 | KR | 10,000/day |
| **Finnhub** | 미국 뉴스 | US | 60/min (free tier) |
| **NewsAPI** | 글로벌 뉴스 | US | 100/day (free tier) |
| **OpenAI API** | LLM (GPT-4/GPT-3.5) | - | Usage-based |
| **AWS Bedrock** | LLM (Claude 3.5 Sonnet) | - | Usage-based |
| **yfinance** | 주가 데이터 (검증용) | KR+US | Unofficial (느슨함) |

---

## 3. Data Architecture

### 3.1 Database Schema Overview

**Primary Database:** PostgreSQL (production) / SQLite (MVP)

**Core Tables:**
1. `news_event` — 개별 뉴스 이벤트 (192 tests 통과)
2. `theme_strength` — 일별 테마 강도 집계
3. `prediction_result` — ML 예측 결과 저장
4. `daily_prediction_result` — 일별 예측 검증 결과
5. `theme_prediction_accuracy` — 테마별 예측 정확도
6. `verification_run_log` — 검증 실행 로그

### 3.2 news_event Table

**역할:** 수집된 모든 뉴스 이벤트 저장 (중복 제거 후)

```sql
CREATE TABLE news_event (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    market             VARCHAR(5) NOT NULL,           -- 'KR' | 'US'
    stock_code         VARCHAR(20) NOT NULL,          -- '005930'
    stock_name         VARCHAR(100),                  -- '삼성전자'
    title              VARCHAR(500) NOT NULL,
    summary            VARCHAR(2000),                 -- LLM 요약
    content            VARCHAR(5000),                 -- 본문 (선택)
    sentiment          VARCHAR(10) NOT NULL DEFAULT 'neutral',
    sentiment_score    FLOAT NOT NULL DEFAULT 0.0,    -- -1.0 ~ 1.0
    news_score         FLOAT NOT NULL DEFAULT 0.0,    -- 0 ~ 100
    source             VARCHAR(50) NOT NULL,          -- 'naver' | 'dart' | 'finnhub'
    source_url         VARCHAR(1000) UNIQUE,          -- 중복 제거 키
    theme              VARCHAR(100),                  -- 'AI' | '반도체' | '2차전지'
    kr_impact_themes   VARCHAR(500),                  -- JSON 배열 (추가 테마)
    is_disclosure      BOOLEAN NOT NULL DEFAULT FALSE,
    published_at       TIMESTAMP WITH TIME ZONE,
    created_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX ix_news_event_market_stock ON news_event(market, stock_code);
CREATE INDEX ix_news_event_published ON news_event(published_at);
CREATE INDEX ix_news_event_market ON news_event(market);
CREATE INDEX ix_news_event_stock_code ON news_event(stock_code);
```

**SQLAlchemy Model (app/models/news_event.py):**
```python
class NewsEvent(Base):
    __tablename__ = "news_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    content: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    sentiment: Mapped[str] = mapped_column(
        String(10), nullable=False, default=SentimentEnum.neutral.value
    )
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    news_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True, unique=True)
    theme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    kr_impact_themes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_disclosure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
```

### 3.3 Redis Cache Strategy

**Redis 사용 목적:**
1. **API Response Caching** — 자주 조회되는 데이터 캐싱
2. **Pub/Sub Messaging** — 실시간 속보 이벤트 전파
3. **Rate Limiting** — API 호출 제한 (slowapi)

**Caching Pattern:**
```python
# Key pattern: "cache:{resource}:{identifier}:{market}"
# TTL: 1-5분 (데이터 특성에 따라)

# Example: Top stocks caching
cache_key = f"cache:top_stocks:{market}:limit_{limit}"
cached = redis_client.get(cache_key)
if cached:
    return json.loads(cached)

# ... fetch from DB ...
redis_client.setex(cache_key, 60, json.dumps(data))  # 1분 TTL
```

**Pub/Sub Channels:**
```python
# Channel: breaking_news
# Message format:
{
    "event": "breaking_news",
    "market": "KR",
    "stock_code": "035420",
    "stock_name": "NAVER",
    "title": "NAVER, 대규모 AI 투자 발표",
    "news_score": 90,
    "theme": "AI",
    "sentiment": "positive",
    "timestamp": "2026-02-21T09:15:02Z"
}
```

**Publish Trigger:**
```python
# app/core/pubsub.py
async def publish_breaking_news(news: NewsEvent):
    """속보 이벤트 발행 (score >= 80)."""
    if news.news_score < 80:
        return

    message = {
        "event": "breaking_news",
        "market": news.market,
        "stock_code": news.stock_code,
        "stock_name": news.stock_name,
        "title": news.title,
        "news_score": news.news_score,
        "theme": news.theme,
        "sentiment": news.sentiment,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    await async_redis_client.publish("breaking_news", json.dumps(message))
```

### 3.4 Data Flow

```
External Source → Collector (Raw Items)
                      ↓
                  Deduplication (source_url check)
                      ↓
                  Stock Mapping (title → stock_code)
                      ↓
                  LLM Analysis (sentiment + theme)
                      ↓
                  Scoring Engine (4-factor formula)
                      ↓
                  DB Insert (news_event table)
                      ↓
                  ┌───┴───┐
                  ▼       ▼
          Redis Pub/Sub   Redis Cache
          (breaking)      (API responses)
                  ▼
          StockAgent Subscriber
```

---

## 4. API Architecture

### 4.1 REST API Design

**Base URL:** `http://localhost:8001` (dev) / `https://api.stocknews.io` (prod)

**API Versioning Strategy:**
- v1: Stable endpoints (backward compatible)
- v2: New features (may break compatibility)

**Middleware Stack:**
```python
# app/main.py
app.add_middleware(CORSMiddleware)           # CORS headers
app.add_middleware(RequestLoggingMiddleware) # Structured logging
app.add_middleware(APIVersionMiddleware)     # X-API-Version header
```

**Rate Limiting:**
```python
# All endpoints use slowapi
@router.get("/news/top")
@limiter.limit("60/minute")  # Per IP
async def get_top_news(request: Request, response: Response, ...):
    pass
```

### 4.2 API Endpoints (v1)

#### News Endpoints

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| GET | `/api/v1/news/score` | 종목별 뉴스 스코어 조회 | 60/min |
| GET | `/api/v1/news/top` | 마켓별 Top 종목 | 60/min |
| GET | `/api/v1/news/latest` | 최신 뉴스 목록 (페이지네이션) | 60/min |

**Example: GET /api/v1/news/score**
```http
GET /api/v1/news/score?stock=005930&market=KR

Response 200:
{
  "market": "KR",
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "news_score": 82.5,
  "sentiment": "positive",
  "issue_count": 5,
  "top_themes": ["AI", "반도체"],
  "updated_at": "2026-02-21T09:12:33Z"
}
```

#### Stock Endpoints

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| GET | `/api/v1/stocks/{code}/timeline` | 종목 스코어 타임라인 | 60/min |

**Example: GET /api/v1/stocks/005930/timeline**
```http
GET /api/v1/stocks/005930/timeline?days=7

Response 200:
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "timeline": [
    {
      "date": "2026-02-21",
      "news_score": 82.5,
      "sentiment_avg": 0.6,
      "news_count": 5
    },
    {
      "date": "2026-02-20",
      "news_score": 65.0,
      "sentiment_avg": 0.3,
      "news_count": 3
    }
  ]
}
```

#### Theme Endpoints

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| GET | `/api/v1/themes/strength` | 테마 강도 순위 | 60/min |

#### Prediction Endpoints (Phase 3)

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| GET | `/api/v1/prediction/stock` | 종목 예측 조회 | 60/min |
| GET | `/api/v1/prediction/summary` | 예측 요약 통계 | 60/min |

#### Health & Admin Endpoints

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| GET | `/health` | 서버 상태 확인 | None |
| GET | `/api/versions` | API 버전 정보 | None |
| POST | `/api/v1/collect/trigger` | 수동 수집 트리거 | 10/hour |

### 4.3 WebSocket Design

**Endpoint:** `WS /ws/news`

**Protocol:**
```javascript
// Client → Server (subscribe)
{
  "type": "subscribe",
  "markets": ["KR", "US"]
}

// Server → Client (breaking_news)
{
  "type": "breaking_news",
  "data": {
    "stock_code": "035420",
    "stock_name": "NAVER",
    "title": "NAVER, 대규모 AI 투자 발표",
    "news_score": 90,
    "theme": "AI",
    "timestamp": "2026-02-21T09:15:02Z"
  }
}

// Server → Client (score_update)
{
  "type": "score_update",
  "data": {
    "stock_code": "005930",
    "news_score": 85,
    "previous_score": 72,
    "updated_at": "2026-02-21T09:20:00Z"
  }
}

// Server → Client (heartbeat)
{
  "type": "ping",
  "timestamp": "2026-02-21T09:21:00Z"
}

// Client → Server (heartbeat response)
{
  "type": "pong",
  "timestamp": "2026-02-21T09:21:00Z"
}
```

**Implementation (app/api/websocket.py):**
```python
@router.websocket("/ws/news")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Subscribe to Redis Pub/Sub
    pubsub = async_redis_client.pubsub()
    await pubsub.subscribe("breaking_news")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
    except WebSocketDisconnect:
        await pubsub.unsubscribe("breaking_news")
```

### 4.4 Error Response Format

**Standard Error Schema:**
```json
{
  "detail": "Resource not found",
  "status_code": 404,
  "error_type": "NotFoundError",
  "timestamp": "2026-02-21T09:22:00Z"
}
```

**HTTP Status Codes:**
- `200 OK` — Success
- `400 Bad Request` — Invalid parameters
- `401 Unauthorized` — Missing/invalid API key (if auth enabled)
- `404 Not Found` — Resource not found
- `422 Unprocessable Entity` — Pydantic validation error
- `429 Too Many Requests` — Rate limit exceeded
- `500 Internal Server Error` — Server error (sanitized in production)
- `503 Service Unavailable` — DB/Redis connection failure

---

## 5. ML Pipeline Architecture

### 5.1 Model Training Flow

```
Historical Data (news_event + yfinance prices)
        ↓
Feature Engineering (app/ml/features.py)
  - news_score (avg, max, min)
  - sentiment_score (avg)
  - news_count
  - theme_counts (AI, 반도체, ...)
  - recency_weighted_score
        ↓
Train/Test Split (80/20)
        ↓
Model Training (Random Forest Classifier)
  - n_estimators=100
  - max_depth=10
  - class_weight='balanced'
        ↓
Model Evaluation
  - Accuracy
  - Precision/Recall (per direction)
  - Confusion Matrix
  - Feature Importance
        ↓
Model Serialization (joblib)
  - /models/rf_model_KR.joblib
  - /models/rf_model_US.joblib
        ↓
Model Registry (file-based, future: MLflow)
```

### 5.2 Prediction Flow

```
Real-time Request (GET /api/v1/prediction/stock?code=005930)
        ↓
Load Model from Cache (or disk)
        ↓
Fetch Recent News (last 30 days)
        ↓
Extract Features
  - Calculate news_score_avg
  - Calculate sentiment_avg
  - Count news
  - Identify top themes
        ↓
Model Inference
  - Predict direction (up/down/neutral)
  - Predict probability (confidence)
        ↓
Post-processing
  - Convert to NewsScore-compatible format
  - Add confidence score
        ↓
Response (JSON)
  {
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "direction": "up",
    "score": 78.5,
    "confidence": 0.72,
    "news_count": 12,
    "top_themes": ["AI", "반도체"],
    "predicted_at": "2026-02-21T09:25:00Z"
  }
```

### 5.3 Feature Engineering

**Input Features (app/ml/features.py):**
```python
def extract_features(news_items: list[NewsEvent]) -> dict:
    """뉴스 이벤트에서 ML 피처 추출."""
    if not news_items:
        return default_features()

    return {
        # Score features
        "news_score_avg": mean([n.news_score for n in news_items]),
        "news_score_max": max([n.news_score for n in news_items]),
        "news_score_min": min([n.news_score for n in news_items]),

        # Sentiment features
        "sentiment_score_avg": mean([n.sentiment_score for n in news_items]),
        "positive_count": sum(1 for n in news_items if n.sentiment == "positive"),
        "negative_count": sum(1 for n in news_items if n.sentiment == "negative"),

        # Volume features
        "news_count": len(news_items),
        "disclosure_count": sum(1 for n in news_items if n.is_disclosure),

        # Theme features (one-hot encoding)
        "theme_AI": sum(1 for n in news_items if "AI" in (n.theme or "")),
        "theme_semiconductor": sum(1 for n in news_items if "반도체" in (n.theme or "")),
        "theme_battery": sum(1 for n in news_items if "2차전지" in (n.theme or "")),

        # Recency features
        "recency_weighted_score": calc_recency_weighted_score(news_items),
    }
```

**Target Label:**
```python
# Binary classification: direction (up/down/neutral)
# Label is calculated by comparing next-day price change
if price_change_pct > 1.0:
    label = "up"
elif price_change_pct < -1.0:
    label = "down"
else:
    label = "neutral"
```

### 5.4 Model Performance Metrics

**Current Metrics (Phase 3):**
- **Accuracy:** 62% (KR), 58% (US)
- **Precision (up):** 65% (KR), 60% (US)
- **Recall (up):** 58% (KR), 55% (US)

**Feature Importance (Top 5):**
1. news_score_avg (25%)
2. sentiment_score_avg (18%)
3. news_count (15%)
4. recency_weighted_score (12%)
5. theme_AI (8%)

---

## 6. Deployment Architecture

### 6.1 Docker Setup

**Container Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │   Frontend   │  │   Backend    │  │   PostgreSQL    │ │
│  │   (Nginx)    │  │  (Uvicorn)   │  │   (postgres:15) │ │
│  │   Port 3000  │  │   Port 8001  │  │   Port 5432     │ │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘ │
│         │                 │                    │          │
│         └─────────────────┴────────────────────┘          │
│                           │                               │
│                  ┌────────┴────────┐                      │
│                  │     Redis       │                      │
│                  │  (redis:7)      │                      │
│                  │  Port 6379      │                      │
│                  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**docker-compose.yml:**
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://stocknews:password@db:5432/stocknews
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DART_API_KEY=${DART_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
      - ./models:/app/models
    command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8001
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=stocknews
      - POSTGRES_USER=stocknews
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

### 6.2 CI/CD Pipeline (GitHub Actions)

**Workflow Stages:**
```
┌─────────────┐
│   Push/PR   │
└──────┬──────┘
       │
       ▼
┌────────────────────────────────────┐
│  Stage 1: Lint & Type Check       │
│  - Ruff (backend)                  │
│  - ESLint (frontend)               │
│  - TypeScript check                │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│  Stage 2: Unit Tests               │
│  - Backend: pytest (192 tests)     │
│  - Frontend: vitest (110 tests)    │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│  Stage 3: Integration Tests        │
│  - API integration (30 tests)      │
│  - E2E: Playwright (18 tests)      │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│  Stage 4: Build Docker Images      │
│  - Backend image                   │
│  - Frontend image                  │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│  Stage 5: Deploy (main branch)     │
│  - Push to ECR/Docker Hub          │
│  - Update ECS task definition      │
│  - Rolling update                  │
└────────────────────────────────────┘
```

**.github/workflows/ci.yml:**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"
      - name: Run linter
        run: ruff check .
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run linter
        run: npm run lint
      - name: Run tests
        run: npm test
      - name: Run E2E tests
        run: npx playwright test

  build:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build backend image
        run: docker build -t stocknews-backend:latest ./backend
      - name: Build frontend image
        run: docker build -t stocknews-frontend:latest ./frontend
```

### 6.3 Monitoring & Logging

**Structured Logging (structlog):**
```python
# app/core/logging.py
import structlog

def setup_logging(log_level: str, json_output: bool, app_env: str):
    """Configure structured logging."""
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**Metrics (Prometheus):**
```python
# app/core/monitoring.py
from prometheus_fastapi_instrumentator import Instrumentator

def setup_prometheus(app: FastAPI):
    """Setup Prometheus metrics."""
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

**Error Tracking (Sentry):**
```python
# app/core/monitoring.py
import sentry_sdk

def init_sentry(dsn: str, environment: str, debug: bool):
    """Initialize Sentry SDK."""
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        debug=debug,
        traces_sample_rate=0.1,  # 10% of transactions
    )
```

### 6.4 Production Checklist

- [x] Environment variables externalized (.env)
- [x] Database migrations (Alembic)
- [x] Redis persistence (AOF enabled)
- [x] API rate limiting (slowapi)
- [x] CORS configured
- [x] Health check endpoint
- [x] Structured logging (JSON in production)
- [x] Error tracking (Sentry)
- [x] Metrics endpoint (Prometheus)
- [x] Secrets management (AWS Secrets Manager)
- [ ] SSL/TLS certificates
- [ ] Load balancer (AWS ALB/ELB)
- [ ] Auto-scaling (ECS/K8s)
- [ ] Database backups (automated)
- [ ] Redis backups (RDB + AOF)

---

## 7. Security Architecture

### 7.1 Authentication & Authorization

**API Key Authentication (Optional):**
```python
# app/core/config.py
class Settings(BaseSettings):
    api_key: str = "dev-api-key-change-in-production"
    api_key_next: str = ""  # Key rotation support
    require_auth: bool = False  # Enable in production
```

**Middleware Implementation:**
```python
# app/core/middleware.py (future)
async def api_key_middleware(request: Request, call_next):
    """Validate X-API-Key header."""
    if not settings.require_auth:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if api_key not in [settings.api_key, settings.api_key_next]:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid API key"}
        )

    return await call_next(request)
```

### 7.2 Secrets Management

**AWS Secrets Manager Integration:**
```python
# app/core/secrets.py
import boto3

class AWSSecretsProvider:
    def __init__(self, secret_name: str, region_name: str):
        self.client = boto3.client("secretsmanager", region_name=region_name)
        self.secret_name = secret_name
        self._cache = None

    def get_secret(self, key: str) -> str | None:
        if not self._cache:
            response = self.client.get_secret_value(SecretId=self.secret_name)
            self._cache = json.loads(response["SecretString"])
        return self._cache.get(key)
```

**Configuration Loading:**
```python
# app/core/config.py
def _load_settings_with_secrets() -> Settings:
    """Load settings with AWS Secrets Manager override."""
    base_settings = Settings()

    if not base_settings.secrets_provider:
        return base_settings

    provider = create_secrets_provider(
        base_settings.secrets_provider,
        secret_name=base_settings.secrets_name,
        region_name=base_settings.secrets_region,
    )

    # Override sensitive fields from Secrets Manager
    sensitive_fields = [
        "api_key", "openai_api_key", "dart_api_key",
        "finnhub_api_key", "redis_password", "database_url"
    ]

    for field in sensitive_fields:
        secret_value = provider.get_secret(field)
        if secret_value:
            setattr(base_settings, field, secret_value)

    return base_settings
```

### 7.3 Data Encryption

**In Transit:**
- HTTPS/TLS 1.3 for all API traffic
- Redis TLS connections (optional, via `redis_ssl` config)
- PostgreSQL SSL connections (via `database_ssl_mode` config)

**At Rest:**
- PostgreSQL database encryption (provider-managed)
- Redis AOF/RDB encryption (provider-managed)
- Secrets stored in AWS Secrets Manager (encrypted)

### 7.4 Input Validation

**Pydantic Schema Validation:**
```python
# app/schemas/news.py
from pydantic import BaseModel, field_validator

class NewsScoreRequest(BaseModel):
    stock: str
    market: str = "KR"

    @field_validator("stock")
    @classmethod
    def validate_stock_code(cls, v):
        if not v or len(v) > 20:
            raise ValueError("stock code must be 1-20 characters")
        return v

    @field_validator("market")
    @classmethod
    def validate_market(cls, v):
        if v not in ["KR", "US"]:
            raise ValueError("market must be KR or US")
        return v
```

**SQL Injection Protection:**
- SQLAlchemy ORM (parameterized queries)
- No raw SQL execution with user input

**XSS Protection:**
- Frontend: React escapes by default
- Backend: Content-Type headers enforced

### 7.5 Rate Limiting

**Implementation (slowapi):**
```python
# app/core/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri="redis://localhost:6379/1",
)
```

**Per-Endpoint Limits:**
```python
@router.get("/news/top")
@limiter.limit("60/minute")
async def get_top_news(...):
    pass

@router.post("/collect/trigger")
@limiter.limit("10/hour")  # Stricter for admin endpoints
async def trigger_collection(...):
    pass
```

---

## 8. Integration Architecture

### 8.1 StockAgent Integration Contract

**Provider:** StockNews (this system)
**Consumer:** StockAgent (~/AgentDev/StockAgent)

**REST API Contract:**
```
GET /api/v1/news/score?stock={code}&market={KR|US}

Response (MUST be backward compatible):
{
  "market": "KR",
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "news_score": 82.5,         // 0-100, REQUIRED
  "sentiment": "positive",     // "positive"|"neutral"|"negative", REQUIRED
  "issue_count": 5,            // REQUIRED
  "top_themes": ["AI", "반도체"], // OPTIONAL (can be empty)
  "updated_at": "2026-02-21T09:12:33Z" // ISO 8601, REQUIRED
}

Rules:
- Existing fields MUST NOT be removed or renamed
- New fields MAY be added (consumers ignore unknown fields)
- Response time target: <200ms (cached), <2s (uncached)
```

**Redis Pub/Sub Contract:**
```
Channel: breaking_news

Message format (MUST be backward compatible):
{
  "type": "breaking_news",
  "stock_code": "005930",       // REQUIRED
  "title": "삼성전자 실적 발표",  // REQUIRED
  "score": 85.5,                // 0-100, REQUIRED
  "sentiment": 0.8,             // -1.0 ~ 1.0, REQUIRED
  "market": "KR"                // "KR"|"US", REQUIRED
}

Trigger condition: score >= 80.0
```

### 8.2 Consumer-Driven Contract Testing

**StockAgent Test (Consumer Side):**
```python
# StockAgent: tests/integration/test_stocknews_contract.py
def test_news_score_api_contract():
    """Verify StockNews API contract."""
    response = requests.get(
        "http://localhost:8001/api/v1/news/score",
        params={"stock": "005930", "market": "KR"}
    )
    assert response.status_code == 200
    data = response.json()

    # Required fields
    assert "market" in data
    assert "stock_code" in data
    assert "news_score" in data
    assert "sentiment" in data
    assert "issue_count" in data
    assert "updated_at" in data

    # Type validation
    assert isinstance(data["news_score"], (int, float))
    assert 0 <= data["news_score"] <= 100
    assert data["sentiment"] in ["positive", "neutral", "negative"]
```

### 8.3 Cross-Project Dependencies

**Shared Contracts Repository:**
```
~/AgentDev/shared/contracts/
├── stocknews-api-v1.json          # OpenAPI spec
├── redis-messages.json            # Pub/Sub message schemas
└── README.md                      # Integration guidelines
```

**Version Management:**
```json
// shared/contracts/stocknews-api-v1.json
{
  "version": "1.0.0",
  "endpoints": {
    "/api/v1/news/score": {
      "required_fields": ["market", "stock_code", "news_score", "sentiment", "issue_count", "updated_at"],
      "deprecated_fields": []
    }
  }
}
```

---

## Document End

**최종 검증일:** 2026-02-21
**검증 항목:**
- Backend 192 tests 통과
- Frontend 110 unit tests + 18 E2E tests 통과
- Build 성공 (tsc + vite build)
- API 엔드포인트 동작 확인
- Redis Pub/Sub 동작 확인
- Docker Compose 기동 확인

**관련 문서:**
- `docs/StockNews-v1.0.md` — 전체 시스템 설계서
- `docs/PredictionVerification-Architecture.md` — 예측 검증 시스템 설계
- `CLAUDE.md` — 프로젝트별 Claude 가이드
- `~/AgentDev/CLAUDE.md` — 크로스 프로젝트 통합 가이드
