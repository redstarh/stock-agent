# StockNews v1.0 설계서

## (한국/미국 공통 뉴스 인텔리전스 시스템 — Frontend + Backend 통합 설계)

---

# 1. 시스템 목적

자동매매 시스템에서 활용할 **뉴스 인텔리전스 서비스(News Intelligence Service)**로, 다음 기능을 담당한다:

* 전일/실시간 뉴스 수집
* 실시간 이슈 감지
* 종목/테마 매핑
* News Score 생성
* **뉴스 대시보드 제공 (신규)**

### StockAgent와의 관계

* StockNews는 **독립 서비스**로 운영되며, StockAgent-KR / StockAgent-US에 REST API와 Redis Pub/Sub으로 데이터를 공급한다.
* StockAgent는 StockNews의 소비자(Consumer)이며, StockNews는 StockAgent에 의존하지 않는다.

### MVP 범위

* **Phase 1 MVP**: 한국 시장 뉴스 수집(네이버 + DART) + 기본 스코어링 + REST API + React 대시보드
* 미국 시장, AI 학습 모델은 Phase 2 이후

---

# 2. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ 대시보드   │  │ 종목 상세  │  │ 테마분석  │  │ 실시간 알림  │ │
│  └─────┬─────┘  └─────┬─────┘  └────┬─────┘  └──────┬───────┘ │
│        │              │              │               │          │
│        └──────────────┴──────┬───────┴───────────────┘          │
│                              │ REST API / WebSocket              │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                        Backend (FastAPI)                         │
│                              │                                   │
│  ┌───────────────────────────┴────────────────────────────────┐ │
│  │                    REST API + WebSocket                     │ │
│  └───────────────────────────┬────────────────────────────────┘ │
│                              │                                   │
│  ┌──────────┐  ┌─────────────┴───────────┐  ┌────────────────┐ │
│  │  News    │  │   News Processing       │  │  News Scoring  │ │
│  │ Collector│→│  (종목매핑/테마/감성)     │→│    Engine      │ │
│  └────┬─────┘  └─────────────────────────┘  └───────┬────────┘ │
│       │                                              │          │
│  ┌────┴──────────────────────────────────────────────┴───────┐ │
│  │              PostgreSQL / SQLite + Redis                    │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │
┌────────┴────────────────────────────────┐
│          외부 뉴스 소스                   │
│  - 네이버 금융 뉴스                      │
│  - DART 공시 API                         │
│  - RSS 금융 뉴스 피드                    │
│  - Finnhub / NewsAPI (Phase 2)           │
└──────────────────────────────────────────┘
```

---

# 3. 기술 스택

## 3.1 Backend

| 구분 | 기술 | 용도 |
|------|------|------|
| 언어 | Python 3.12+ (개발환경 3.13) | 서버 개발 |
| 웹 프레임워크 | FastAPI | REST API + WebSocket |
| ORM | SQLAlchemy 2.0 | 데이터베이스 접근 |
| DB (MVP) | SQLite | 로컬 개발용 |
| DB (운영) | PostgreSQL 15+ | 프로덕션 |
| 캐시/Pub-Sub | Redis 7+ | 실시간 이벤트, 캐시 |
| 스케줄러 | APScheduler | 배치 수집 |
| NLP/분석 | OpenAI API | 뉴스 요약, 감성 분석 |
| 종목 매핑 | KoNLPy / Regex | 한국어 종목명 추출 |

## 3.2 Frontend

| 구분 | 기술 | 용도 |
|------|------|------|
| 언어 | TypeScript 5+ | 타입 안전 개발 |
| UI 프레임워크 | React 18 | 컴포넌트 기반 UI |
| 빌드 도구 | Vite 5+ | 빠른 빌드/HMR |
| 서버 상태 | TanStack Query v5 | API 데이터 캐싱/동기화 |
| 차트 | Recharts | 스코어/감성 시각화 |
| 스타일링 | Tailwind CSS 3 | 유틸리티 기반 CSS |
| 라우팅 | React Router v6 | SPA 라우팅 |
| 실시간 | WebSocket (native) | 속보 알림 |

## 3.3 공통

| 구분 | 기술 | 용도 |
|------|------|------|
| 컨테이너 | Docker / Docker Compose | 개발/배포 환경 |
| 버전 관리 | Git | 소스 코드 관리 |
| 린터/포매터 | Ruff (Python), ESLint + Prettier (TS) | 코드 품질 |

---

# 4. 프로젝트 디렉토리 구조

```
StockNews/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # API 라우터 통합
│   │   │   ├── news.py          # /news 엔드포인트
│   │   │   ├── themes.py        # /theme 엔드포인트
│   │   │   ├── stocks.py        # /stocks 엔드포인트
│   │   │   └── health.py        # /health 엔드포인트
│   │   ├── collectors/
│   │   │   ├── __init__.py
│   │   │   ├── naver.py         # 네이버 뉴스 크롤러
│   │   │   ├── dart.py          # DART 공시 API
│   │   │   ├── rss.py           # RSS 피드 파서
│   │   │   └── scheduler.py     # 수집 스케줄러
│   │   ├── processing/
│   │   │   ├── __init__.py
│   │   │   ├── stock_mapper.py  # 종목 코드 매핑
│   │   │   ├── theme_classifier.py  # 테마 분류
│   │   │   ├── sentiment.py     # 감성 분석 (LLM)
│   │   │   └── dedup.py         # 중복 제거
│   │   ├── scoring/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py        # 스코어링 엔진
│   │   │   └── aggregator.py    # 종목/테마별 집계
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── news_event.py    # news_event 테이블
│   │   │   └── theme_strength.py # theme_strength 테이블
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── news.py          # 뉴스 관련 Pydantic 스키마
│   │   │   ├── theme.py         # 테마 관련 스키마
│   │   │   └── common.py        # 공통 스키마
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── config.py        # 환경 설정
│   │       ├── database.py      # DB 연결
│   │       └── redis.py         # Redis 연결
│   ├── alembic/                 # DB 마이그레이션
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py          # pytest 공통 fixture
│   │   ├── unit/
│   │   │   ├── test_scoring.py
│   │   │   ├── test_stock_mapper.py
│   │   │   └── test_dedup.py
│   │   └── integration/
│   │       ├── test_api_news.py
│   │       └── test_collectors.py
│   ├── pyproject.toml
│   └── alembic.ini              # DB 마이그레이션 설정
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # 앱 진입점
│   │   ├── App.tsx              # 라우팅 설정
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── news/
│   │   │   │   ├── NewsList.tsx
│   │   │   │   ├── NewsCard.tsx
│   │   │   │   ├── NewsScoreBadge.tsx
│   │   │   │   └── TopStockCards.tsx
│   │   │   ├── charts/
│   │   │   │   ├── ScoreTimeline.tsx
│   │   │   │   ├── SentimentPie.tsx
│   │   │   │   └── ThemeStrengthChart.tsx
│   │   │   └── common/
│   │   │       ├── Loading.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       ├── Toast.tsx
│   │   │       ├── MarketSelector.tsx
│   │   │       ├── SentimentIndicator.tsx
│   │   │       └── NotificationBell.tsx
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── StockDetailPage.tsx
│   │   │   └── ThemeAnalysisPage.tsx
│   │   ├── hooks/
│   │   │   ├── useNewsScore.ts
│   │   │   ├── useTopNews.ts
│   │   │   ├── useThemeStrength.ts
│   │   │   └── useWebSocket.ts
│   │   ├── api/
│   │   │   ├── client.ts        # axios/fetch 인스턴스
│   │   │   ├── news.ts          # 뉴스 API 함수
│   │   │   ├── themes.ts        # 테마 API 함수
│   │   │   └── stocks.ts        # 종목 API 함수
│   │   ├── types/
│   │   │   ├── news.ts          # 뉴스 타입 정의
│   │   │   ├── theme.ts         # 테마 타입 정의
│   │   │   └── api.ts           # API 응답 타입
│   │   └── utils/
│   │       ├── format.ts        # 날짜/숫자 포맷팅
│   │       └── constants.ts     # 상수 정의
│   ├── tests/
│   │   ├── setup.ts             # 테스트 설정
│   │   ├── components/
│   │   └── hooks/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── docs/
│   ├── StockNews.md             # 초기 설계서 (archived)
│   ├── StockNews-v0.9.md        # 이전 버전
│   └── StockNews-v1.0.md        # 현재 문서
├── docker-compose.yml
└── README.md
```

---

# 5. Backend 모듈 상세

## 5.1 News Collector

뉴스 소스로부터 데이터를 수집하는 모듈.

### 기능

* 전일 뉴스 배치 수집 (Batch)
* 장중 뉴스 근실시간 수집 (Near Real-time, 5분 주기)
* DART 공시 이벤트 수집
* RSS 피드 수집

### 필요 외부 API

**Phase 1 (한국)**
* DART Open API — 공시 정보
* 네이버 금융 뉴스 — 크롤링
* RSS 금융 뉴스 피드

**Phase 2 (미국 확장)**
* Finnhub News API
* NewsAPI (글로벌)

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* 네이버 뉴스 크롤러가 최소 10건의 뉴스를 정상 수집하는 것을 테스트로 확인
* DART API 호출 후 JSON 파싱이 에러 없이 완료
* 동일 URL/제목의 뉴스가 중복 저장되지 않음
* 스케줄러가 설정된 주기에 맞게 수집을 트리거하는 것을 로그로 확인

---

## 5.2 News Processing Module

수집된 뉴스를 분석하고 구조화하는 모듈.

### 기능

* 종목 코드 매핑 (예: "삼성전자" → 005930)
* 테마 분류 (AI, 반도체, 2차전지 등)
* LLM 기반 뉴스 요약
* 감성 분석 (positive / neutral / negative)

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* "삼성전자 실적 발표" 뉴스가 종목코드 005930에 매핑됨
* "AI 반도체 수요 증가" 뉴스가 "AI", "반도체" 테마로 분류됨
* 감성 분석 결과가 positive/neutral/negative 중 하나를 반환
* KOSPI 200 종목 중 종목명→코드 매핑 정확도 90% 이상

---

## 5.3 News Scoring Engine (핵심)

뉴스 데이터를 종합하여 종목별 뉴스 점수를 산출하는 엔진.

### 점수 산식

```
News Score =
  (Recency × 0.4) +
  (Frequency × 0.3) +
  (Sentiment × 0.2) +
  (Disclosure Bonus × 0.1)
```

| 요소 | 설명 | 범위 |
|------|------|------|
| Recency | 뉴스 최신성 (시간 감쇠) | 0–100 |
| Frequency | 일정 기간 내 뉴스 빈도 | 0–100 |
| Sentiment | 감성 분석 점수 | 0–100 |
| Disclosure Bonus | 공시 포함 여부 가산점 | 0 또는 100 |

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* 동일 종목의 뉴스가 많을수록 Frequency 점수가 높아짐
* 최신 뉴스일수록 Recency 점수가 높음
* 공시가 포함된 종목의 점수가 공시 없는 종목보다 높음 (다른 조건 동일 시)
* 최종 점수가 0–100 범위 내에서 산출됨

---

## 5.4 REST API

FastAPI 기반 REST API 서버.

### 엔드포인트 명세

#### `GET /news/score`

종목별 뉴스 점수 조회.

**요청 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| stock | string | Y | 종목 코드 (예: 005930) |
| market | string | N | 마켓 구분 (KR/US, 기본값: KR) |

**응답:**

```json
{
  "market": "KR",
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "news_score": 82,
  "sentiment": "positive",
  "issue_count": 5,
  "top_themes": ["AI", "반도체"],
  "updated_at": "2026-02-17T09:12:33"
}
```

#### `GET /news/top`

마켓별 뉴스 점수 상위 종목 조회.

**요청 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| market | string | Y | KR 또는 US |
| limit | int | N | 반환 개수 (기본값: 20) |

**응답:**

```json
{
  "market": "KR",
  "items": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "news_score": 82,
      "sentiment": "positive",
      "issue_count": 5
    },
    {
      "stock_code": "035420",
      "stock_name": "NAVER",
      "news_score": 75,
      "sentiment": "neutral",
      "issue_count": 3
    }
  ],
  "updated_at": "2026-02-17T09:15:00"
}
```

#### `GET /news/latest`

최신 뉴스 목록 조회.

**요청 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| market | string | N | KR/US (기본값: 전체) |
| limit | int | N | 반환 개수 (기본값: 50) |
| offset | int | N | 페이지네이션 오프셋 |

**응답:**

```json
{
  "items": [
    {
      "id": 1234,
      "title": "삼성전자, AI 반도체 수출 역대 최대",
      "market": "KR",
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "theme": "AI",
      "sentiment": "positive",
      "news_score": 88,
      "source": "네이버금융",
      "source_url": "https://finance.naver.com/news/...",
      "published_at": "2026-02-17T08:30:00"
    }
  ],
  "total": 150,
  "offset": 0,
  "limit": 50
}
```

#### `GET /stocks/{code}/timeline`

종목의 뉴스 스코어 타임라인 조회.

**경로 파라미터:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| code | string | 종목 코드 |

**요청 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| days | int | N | 조회 기간 일수 (기본값: 7) |

**응답:**

```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "timeline": [
    {
      "date": "2026-02-17",
      "news_score": 82,
      "sentiment_avg": 0.6,
      "news_count": 5
    },
    {
      "date": "2026-02-16",
      "news_score": 65,
      "sentiment_avg": 0.3,
      "news_count": 3
    }
  ]
}
```

#### `GET /theme/strength`

테마 강도 순위 조회.

**요청 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| market | string | N | KR/US (기본값: KR) |
| limit | int | N | 반환 개수 (기본값: 10) |

**응답:**

```json
{
  "market": "KR",
  "themes": [
    {
      "theme": "AI",
      "strength_score": 92,
      "news_count": 45,
      "avg_sentiment": 0.7,
      "top_stocks": ["005930", "035420"]
    },
    {
      "theme": "2차전지",
      "strength_score": 78,
      "news_count": 30,
      "avg_sentiment": 0.4,
      "top_stocks": ["373220", "006400"]
    }
  ],
  "date": "2026-02-17"
}
```

#### `GET /health`

서버 상태 확인.

**응답:**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "db": "connected",
  "redis": "connected",
  "last_collection": "2026-02-17T09:00:00"
}
```

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* 모든 엔드포인트가 정의된 스키마대로 응답을 반환
* 잘못된 파라미터에 대해 422 에러를 반환
* `/health` 엔드포인트가 DB/Redis 연결 상태를 정확히 보고
* Swagger UI (`/docs`)에서 모든 API를 확인 가능

---

## 5.5 Redis Pub/Sub (속보 이벤트)

실시간 속보 뉴스를 이벤트로 전파하는 모듈.

### Channel

* `news_breaking_kr` — 한국 속보
* `news_breaking_us` — 미국 속보

### 메시지 포맷

```json
{
  "event": "breaking_news",
  "market": "KR",
  "stock_code": "035420",
  "stock_name": "NAVER",
  "title": "NAVER, 대규모 AI 투자 발표",
  "news_score": 90,
  "theme": "AI",
  "sentiment": "positive",
  "timestamp": "2026-02-17T09:15:02"
}
```

### WebSocket 엔드포인트

Frontend 실시간 연동을 위한 WebSocket 엔드포인트:

* `WS /ws/news` — 속보 뉴스 실시간 스트림

**WebSocket 메시지 프로토콜:**

```json
// 서버 → 클라이언트
{
  "type": "breaking_news",
  "data": {
    "stock_code": "035420",
    "stock_name": "NAVER",
    "title": "NAVER, 대규모 AI 투자 발표",
    "news_score": 90,
    "theme": "AI",
    "timestamp": "2026-02-17T09:15:02"
  }
}

// 서버 → 클라이언트 (스코어 변동)
{
  "type": "score_update",
  "data": {
    "stock_code": "005930",
    "news_score": 85,
    "previous_score": 72,
    "updated_at": "2026-02-17T09:20:00"
  }
}
```

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* Redis에 뉴스 이벤트를 발행하면 구독자가 수신
* WebSocket 클라이언트가 연결 후 속보 이벤트를 수신
* 속보 점수 임계값(예: 80 이상)을 초과하는 뉴스만 발행됨

---

# 6. Frontend 모듈 상세

## 6.1 대시보드 (메인 페이지)

전체 뉴스 인텔리전스 현황을 한눈에 파악하는 메인 페이지.

### 기능

* 마켓별 Top 종목 뉴스 스코어 카드
* 최신 뉴스 피드 (실시간 갱신)
* 테마 강도 요약 차트
* 마켓 전환 (KR / US 탭)

### 주요 컴포넌트

* `DashboardPage` — 페이지 레이아웃
* `TopStockCards` — 상위 종목 스코어 카드 그리드
* `NewsList` + `NewsCard` — 뉴스 피드
* `ThemeStrengthChart` — 테마 강도 바 차트
* `MarketSelector` — KR/US 마켓 탭

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* 페이지 로드 시 `/news/top` API를 호출하여 상위 종목이 표시됨
* 뉴스 카드에 종목명, 스코어, 감성 배지가 모두 표시됨
* KR/US 탭 전환 시 해당 마켓 데이터로 갱신됨
* 로딩 상태와 에러 상태가 적절히 표시됨

---

## 6.2 종목 상세 페이지

개별 종목의 뉴스 데이터를 상세 분석하는 페이지.

### 기능

* 종목 뉴스 스코어 타임라인 차트
* 해당 종목 뉴스 목록
* 감성 분포 (positive/neutral/negative) 파이 차트
* 관련 테마 태그

### 주요 컴포넌트

* `StockDetailPage` — 페이지 레이아웃
* `ScoreTimeline` — 일별 스코어 꺾은선 차트
* `SentimentPie` — 감성 분포 파이 차트
* `NewsList` — 해당 종목 뉴스 필터링 목록

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* `/stocks/005930` 접근 시 삼성전자 뉴스 데이터가 표시됨
* 타임라인 차트에 최근 7일 스코어 추이가 표시됨
* 감성 파이 차트가 positive/neutral/negative 비율을 정확히 반영
* 존재하지 않는 종목코드 접근 시 적절한 에러 메시지 표시

---

## 6.3 테마 분석 페이지

테마별 뉴스 강도를 분석하는 페이지.

### 기능

* 테마 강도 랭킹 차트 (수평 바 차트)
* 테마 선택 시 관련 종목 목록
* 테마별 감성 평균

### 주요 컴포넌트

* `ThemeAnalysisPage` — 페이지 레이아웃
* `ThemeStrengthChart` — 테마 강도 바 차트
* `ThemeStockList` — 테마별 종목 목록
* `SentimentIndicator` — 감성 지표 뱃지

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* `/theme/strength` API 데이터가 차트로 정확히 렌더링됨
* 테마 클릭 시 해당 테마의 top_stocks 종목이 표시됨
* 강도 점수 순으로 정렬되어 표시됨

---

## 6.4 실시간 알림

WebSocket 기반 속보 뉴스 실시간 알림 시스템.

### 기능

* WebSocket 연결로 속보 뉴스 실시간 수신
* 토스트 알림 표시
* 알림 히스토리 (최근 N건)

### 주요 컴포넌트

* `useWebSocket` — WebSocket 연결 관리 훅
* `Toast` — 토스트 알림 컴포넌트
* `NotificationBell` — 헤더 알림 아이콘 + 배지

> 상세 Task는 [Section 9. 개발 프로세스](#9-개발-프로세스)를 참조하세요.

### 검증 기준

* 서버에서 속보 이벤트 발행 시 클라이언트에 토스트 알림이 표시됨
* WebSocket 연결 끊김 후 자동 재연결됨
* 알림 아이콘 배지에 읽지 않은 알림 수가 표시됨

---

# 7. API 인터페이스 설계

## 7.1 REST API 요약

| Method | Endpoint | 설명 | 요청 | 응답 |
|--------|----------|------|------|------|
| GET | `/news/score` | 종목별 뉴스 스코어 | `?stock=005930&market=KR` | NewsScore |
| GET | `/news/top` | 마켓별 Top 종목 | `?market=KR&limit=20` | NewsTopList |
| GET | `/news/latest` | 최신 뉴스 목록 | `?market=KR&limit=50&offset=0` | NewsList |
| GET | `/stocks/{code}/timeline` | 종목 스코어 타임라인 | `?days=7` | StockTimeline |
| GET | `/theme/strength` | 테마 강도 순위 | `?market=KR&limit=10` | ThemeStrengthList |
| GET | `/health` | 서버 상태 확인 | - | HealthStatus |

## 7.2 Pydantic 스키마 정의

```python
# schemas/common.py
from enum import Enum

class SentimentEnum(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
```

```python
# schemas/news.py
from .common import SentimentEnum

class NewsScoreResponse(BaseModel):
    market: str           # "KR" | "US"
    stock_code: str       # "005930"
    stock_name: str       # "삼성전자"
    news_score: int       # 0-100
    sentiment: SentimentEnum
    issue_count: int
    top_themes: list[str]
    updated_at: datetime

class NewsItem(BaseModel):
    id: int
    title: str
    market: str
    stock_code: str
    stock_name: str
    theme: str
    sentiment: SentimentEnum
    news_score: int
    source: str
    source_url: str | None = None
    published_at: datetime

class NewsListResponse(BaseModel):
    items: list[NewsItem]
    total: int
    offset: int
    limit: int

class TopStockItem(BaseModel):
    stock_code: str
    stock_name: str
    news_score: int
    sentiment: SentimentEnum
    issue_count: int

class NewsTopResponse(BaseModel):
    market: str
    items: list[TopStockItem]
    updated_at: datetime
```

```python
# schemas/theme.py
class ThemeItem(BaseModel):
    theme: str
    strength_score: int
    news_count: int
    avg_sentiment: float
    top_stocks: list[str]

class ThemeStrengthResponse(BaseModel):
    market: str
    themes: list[ThemeItem]
    date: str

# schemas/common.py (continued)
class TimelinePoint(BaseModel):
    date: str
    news_score: int
    sentiment_avg: float
    news_count: int

class StockTimelineResponse(BaseModel):
    stock_code: str
    stock_name: str
    timeline: list[TimelinePoint]

class HealthResponse(BaseModel):
    status: str
    version: str
    db: str
    redis: str
    last_collection: datetime | None
```

## 7.3 WebSocket 이벤트 명세

| 이벤트 타입 | 방향 | 설명 | 데이터 |
|------------|------|------|--------|
| `breaking_news` | Server → Client | 속보 뉴스 | stock_code, title, news_score, theme |
| `score_update` | Server → Client | 스코어 변동 | stock_code, news_score, previous_score |
| `ping` | Server → Client | Heartbeat | timestamp |
| `pong` | Client → Server | Heartbeat 응답 | timestamp |

## 7.4 TypeScript 타입 정의

```typescript
// types/news.ts
type Sentiment = 'positive' | 'neutral' | 'negative';

interface NewsScore {
  market: string;
  stock_code: string;
  stock_name: string;
  news_score: number;
  sentiment: Sentiment;
  issue_count: number;
  top_themes: string[];
  updated_at: string;
}

interface NewsItem {
  id: number;
  title: string;
  market: string;
  stock_code: string;
  stock_name: string;
  theme: string;
  sentiment: Sentiment;
  news_score: number;
  source: string;
  source_url: string | null;
  published_at: string;
}

interface TimelinePoint {
  date: string;
  news_score: number;
  sentiment_avg: number;
  news_count: number;
}

interface StockTimeline {
  stock_code: string;
  stock_name: string;
  timeline: TimelinePoint[];
}

// types/theme.ts
interface ThemeItem {
  theme: string;
  strength_score: number;
  news_count: number;
  avg_sentiment: number;
  top_stocks: string[];
}

// types/api.ts
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

interface WebSocketMessage {
  type: 'breaking_news' | 'score_update' | 'ping';
  data: Record<string, unknown>;
}
```

---

# 8. 데이터베이스 설계

## 8.1 news_event

개별 뉴스 이벤트를 저장하는 핵심 테이블.

```sql
CREATE TABLE news_event (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,  -- PK (PostgreSQL: SERIAL)
    market        VARCHAR(2) NOT NULL,                -- 'KR' | 'US'
    stock_code    VARCHAR(10) NOT NULL,               -- 종목 코드
    stock_name    VARCHAR(100),                       -- 종목명
    title         VARCHAR(500) NOT NULL,              -- 뉴스 제목
    summary       TEXT,                               -- LLM 요약 (선택)
    theme         VARCHAR(50),                        -- 테마 분류
    sentiment     VARCHAR(10) NOT NULL DEFAULT 'neutral', -- positive/neutral/negative
    sentiment_score FLOAT DEFAULT 0.0,                -- 감성 점수 (-1.0 ~ 1.0)
    news_score    INTEGER DEFAULT 0,                  -- 최종 뉴스 점수 (0-100)
    source        VARCHAR(50) NOT NULL,               -- 출처 (naver/dart/rss 등)
    source_url    VARCHAR(500),                       -- 원문 URL
    is_disclosure BOOLEAN DEFAULT FALSE,              -- 공시 여부
    collected_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 수집 시각
    published_at  TIMESTAMP,                          -- 기사 발행 시각
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_news_stock_code ON news_event(stock_code);
CREATE INDEX idx_news_market ON news_event(market);
CREATE INDEX idx_news_theme ON news_event(theme);
CREATE INDEX idx_news_published_at ON news_event(published_at);
CREATE INDEX idx_news_score ON news_event(news_score DESC);
CREATE UNIQUE INDEX idx_news_dedup ON news_event(source_url);
```

## 8.2 theme_strength

일별 테마 강도 집계 테이블.

```sql
CREATE TABLE theme_strength (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            DATE NOT NULL,                     -- 집계 날짜
    market          VARCHAR(2) NOT NULL,               -- 'KR' | 'US'
    theme           VARCHAR(50) NOT NULL,              -- 테마명
    news_count      INTEGER DEFAULT 0,                 -- 해당 테마 뉴스 수
    avg_sentiment   FLOAT DEFAULT 0.0,                 -- 평균 감성 점수
    strength_score  INTEGER DEFAULT 0,                 -- 테마 강도 점수 (0-100)
    top_stocks      TEXT,                              -- 상위 종목 코드 (JSON 배열)
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_theme_date ON theme_strength(date);
CREATE INDEX idx_theme_market ON theme_strength(market);
CREATE UNIQUE INDEX idx_theme_unique ON theme_strength(date, market, theme);
```

---

# 9. 개발 프로세스

## Phase 1 — MVP (한국 뉴스 + 기본 대시보드)

### 목표

한국 시장 뉴스 수집 → 스코어링 → REST API → 기본 React 대시보드

### Task 순서 및 의존 관계

```
[1] 프로젝트 초기 설정
 │
 ├──→ [2] Backend: DB 모델 + 설정
 │     │
 │     ├──→ [3] Backend: News Collector (네이버 + DART)
 │     │     │
 │     │     └──→ [4] Backend: News Processing (매핑 + 감성)
 │     │           │
 │     │           └──→ [5] Backend: Scoring Engine
 │     │
 │     └──→ [6] Backend: REST API 서버
 │           │
 │           └──→ [7] Backend: Redis Pub/Sub + WebSocket
 │
 ├──→ [8] Frontend: 프로젝트 설정 + 레이아웃
 │     │
 │     ├──→ [9] Frontend: 대시보드 페이지
 │     │
 │     ├──→ [10] Frontend: 종목 상세 페이지
 │     │
 │     ├──→ [11] Frontend: 테마 분석 페이지
 │     │
 │     └──→ [12] Frontend: 실시간 알림
 │
 └──→ [13] 테스트 인프라 구축
```

※ Backend [2]–[7]과 Frontend [8]–[12]는 **병렬 개발 가능** (API 스키마 합의 후)

### 세부 Task

**[1] 프로젝트 초기 설정**
* [ ] Git 저장소 구성 (backend/, frontend/, docs/)
* [ ] Backend: pyproject.toml + 의존성 설치
* [ ] Frontend: Vite + React + TypeScript 프로젝트 생성
* [ ] Docker Compose 기본 설정 (Python + Redis + PostgreSQL)
* [ ] `.env.example` 파일 생성 (Backend + Frontend 환경변수 템플릿)
* [ ] Ruff 린터 설정 (`ruff.toml`)
* [ ] ESLint + Prettier 설정 (Frontend)
* [ ] `.gitignore` 정비 (Python, Node, IDE, 환경변수 파일)
* [ ] `.dockerignore` 파일 생성
* [ ] 검증: `docker-compose up` 으로 모든 서비스 기동 확인

**[2] Backend: DB 모델 + 설정**
* [ ] SQLAlchemy 모델 정의 (news_event, theme_strength)
* [ ] 환경 설정 모듈 (config.py — Pydantic Settings)
* [ ] DB 연결 모듈 (database.py)
* [ ] Redis 연결 모듈 (redis.py)
* [ ] Alembic 마이그레이션 초기 설정 (`alembic.ini` + `alembic/`)
* [ ] 초기 마이그레이션 파일 생성 (news_event, theme_strength)
* [ ] 검증: DB 테이블 생성 및 CRUD 동작 테스트 통과

**[3] Backend: News Collector**
* [ ] 네이버 뉴스 크롤러
* [ ] DART API 수집 모듈
* [ ] RSS 파서
* [ ] 중복 제거 로직
* [ ] APScheduler 스케줄러
* [ ] 수집 실패 시 재시도 로직 (exponential backoff)
* [ ] 검증: 최소 10건 뉴스 수집 + DB 저장 확인

**[4] Backend: News Processing**
* [ ] 종목 사전 구축 (KOSPI 200)
* [ ] 키워드 기반 테마 매핑
* [ ] LLM 감성 분석 파이프라인
* [ ] 검증: 테스트 뉴스 5건에 대해 종목/테마/감성 매핑 정확도 확인

**[5] Backend: Scoring Engine**
* [ ] 점수 계산 로직 (4가지 요소)
* [ ] Disclosure Bonus 판정 로직 (is_disclosure 필드 기반 가산점 계산)
* [ ] 종목별 집계
* [ ] 테마 강도 계산
* [ ] 검증: 시나리오 테스트 — 동일 조건 변경 시 점수 변화 확인

**[6] Backend: REST API 서버**
* [ ] FastAPI 앱 + 라우터 구성
* [ ] 모든 엔드포인트 구현 (`/news/score`, `/news/top`, `/news/latest`, `/stocks/{code}/timeline`, `/theme/strength`, `/health`)
* [ ] `/news/latest` 엔드포인트 명시적 구현 (페이지네이션 포함)
* [ ] Pydantic 스키마 개별 파일 구현 (`schemas/news.py`, `schemas/theme.py`, `schemas/common.py`)
* [ ] Sentiment Enum 정의 (`positive | neutral | negative`)
* [ ] 에러 핸들링 미들웨어 (글로벌 예외 처리 + 표준 에러 응답)
* [ ] CORS 설정
* [ ] 검증: Swagger UI에서 모든 API 호출 성공

**[7] Backend: Redis Pub/Sub + WebSocket**
* [ ] 속보 이벤트 발행 로직
* [ ] WebSocket 엔드포인트
* [ ] WebSocket Heartbeat (ping/pong) 프로토콜 구현
* [ ] 검증: WebSocket 클라이언트로 이벤트 수신 테스트

**[8] Frontend: 프로젝트 설정**
* [ ] Vite + React + TypeScript 초기화
* [ ] Tailwind CSS 설정
* [ ] React Router 라우팅 구성
* [ ] TanStack Query Provider 설정
* [ ] 레이아웃 컴포넌트 (Header, Sidebar, Layout)
* [ ] API 클라이언트 인스턴스 설정 (`api/client.ts` — axios 또는 fetch 래퍼)
* [ ] API 함수 파일 생성 (`api/news.ts`, `api/themes.ts`, `api/stocks.ts`)
* [ ] TypeScript 타입 정의 파일 (`types/news.ts`, `types/theme.ts`, `types/api.ts`)
* [ ] 유틸리티 파일 (`utils/format.ts`, `utils/constants.ts`)
* [ ] 공통 컴포넌트 구현 (`Loading.tsx`, `ErrorBoundary.tsx`)
* [ ] 검증: `npm run dev` 로 빈 대시보드 페이지 렌더링 확인

**[9] Frontend: 대시보드**
* [ ] Top 종목 카드 그리드
* [ ] 뉴스 피드 리스트
* [ ] 테마 강도 요약 차트
* [ ] 마켓 탭 (KR/US)
* [ ] 검증: API 연동 후 실제 데이터로 대시보드 정상 렌더링

**[10] Frontend: 종목 상세**
* [ ] 스코어 타임라인 차트
* [ ] 감성 분포 파이 차트
* [ ] 종목 뉴스 목록
* [ ] 검증: `/stocks/005930` 접근 시 삼성전자 데이터 표시

**[11] Frontend: 테마 분석**
* [ ] 테마 강도 바 차트
* [ ] 테마별 종목 목록
* [ ] 검증: 테마 차트 렌더링 + 클릭 시 관련 종목 표시

**[12] Frontend: 실시간 알림**
* [ ] WebSocket 연결 훅
* [ ] 토스트 알림
* [ ] 알림 히스토리
* [ ] 검증: 서버 속보 이벤트 → 클라이언트 토스트 표시

**[13] 테스트 인프라 구축**
* [ ] Backend: pytest 설정 + `conftest.py` fixture (SQLite in-memory DB, 샘플 데이터)
* [ ] Backend: 주요 단위 테스트 작성 (scoring engine, stock_mapper, dedup)
* [ ] Frontend: Vitest + React Testing Library 설정
* [ ] Frontend: MSW(Mock Service Worker) 핸들러 설정
* [ ] 검증: `pytest` 및 `npm run test` 실행 시 테스트 통과

---

## Phase 2 — 분석 고도화 + 실시간 강화

### 목표

LLM 분석 정확도 향상 + 실시간 뉴스 파이프라인 + 미국 뉴스 소스 통합

### Task

* [ ] LLM 프롬프트 튜닝 (감성 분석 정확도 개선)
* [ ] 뉴스 요약 기능 추가
* [ ] Finnhub / NewsAPI 연동 (미국 시장)
* [ ] 실시간 수집 주기 단축 (5분 → 1분)
* [ ] Frontend 차트 인터랙션 강화 (드릴다운, 필터)

### 검증 기준

* 미국 뉴스 소스(Finnhub/NewsAPI)에서 일 10건 이상 수집 정상 동작
* 감성 분석 정확도: 수동 검증 100건 샘플 중 80% 이상 일치
* 뉴스 수집 주기 1분 이내 달성 확인
* 뉴스 요약 기능이 원문 대비 핵심 정보를 포함 (수동 검증 20건)

---

## Phase 3 — AI 학습 모델 + 고도화

### 목표

뉴스 영향도 학습 모델 도입 + 예측 기능

### Task

* [ ] 뉴스 → 주가 변동 상관관계 데이터 수집
* [ ] AI 기반 뉴스 영향도 학습 모델 구축
* [ ] 예측 점수 기능 추가
* [ ] 대시보드에 예측 뷰 추가

### 검증 기준

* 학습 데이터 최소 6개월 축적
* 예측 모델 백테스트 정확도 60% 이상 (뉴스 발생 후 1일 주가 방향 예측)
* 예측 점수와 실제 주가 변동의 상관계수 0.3 이상

---

# 10. 테스트 전략

## 10.1 Backend 테스트

### 단위 테스트 (pytest)

| 대상 | 테스트 항목 | 파일 |
|------|-----------|------|
| Scoring Engine | 점수 계산 로직, 경계값 | `tests/unit/test_scoring.py` |
| Stock Mapper | 종목명 → 코드 매핑 | `tests/unit/test_stock_mapper.py` |
| Dedup | 중복 판별 로직 | `tests/unit/test_dedup.py` |
| Theme Classifier | 테마 분류 정확성 | `tests/unit/test_theme_classifier.py` |

### 통합 테스트

| 대상 | 테스트 항목 | 파일 |
|------|-----------|------|
| REST API | 엔드포인트 요청/응답 | `tests/integration/test_api_news.py` |
| Collectors | 외부 API 호출 (mock) | `tests/integration/test_collectors.py` |
| DB | CRUD 동작 | `tests/integration/test_database.py` |

### Fixture 전략

```python
# tests/conftest.py
@pytest.fixture
def db_session():
    """테스트용 SQLite in-memory DB 세션"""

@pytest.fixture
def sample_news_events():
    """테스트용 뉴스 이벤트 데이터"""

@pytest.fixture
def mock_naver_response():
    """네이버 뉴스 크롤링 mock 응답"""
```

### 실행 방법

```bash
cd backend
pytest tests/unit -v              # 단위 테스트
pytest tests/integration -v       # 통합 테스트
pytest --cov=app --cov-report=html  # 커버리지
```

## 10.2 Frontend 테스트

### 단위 테스트 (Vitest + React Testing Library)

| 대상 | 테스트 항목 | 파일 |
|------|-----------|------|
| NewsCard | 렌더링, 스코어 색상 | `tests/components/NewsCard.test.tsx` |
| ScoreTimeline | 차트 렌더링 | `tests/components/ScoreTimeline.test.tsx` |
| useNewsScore | API 호출, 에러 처리 | `tests/hooks/useNewsScore.test.ts` |

### API Mocking (MSW)

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/news/top', () =>
    HttpResponse.json({ market: 'KR', items: [...] })
  ),
];
```

### 실행 방법

```bash
cd frontend
npm run test              # Vitest 실행
npm run test:coverage     # 커버리지
```

## 10.3 E2E 테스트 (선택)

Playwright로 주요 사용자 시나리오 테스트:

* [ ] 대시보드 → 종목 클릭 → 상세 페이지 이동
* [ ] 테마 분석 페이지 → 테마 클릭 → 종목 목록 표시
* [ ] 속보 알림 수신 확인

## 10.4 커버리지 목표

| 범위 | 목표 |
|------|------|
| Backend 단위 테스트 | 80% 이상 |
| Backend 통합 테스트 | 주요 API 전체 커버 |
| Frontend 컴포넌트 | 주요 컴포넌트 70% 이상 |
| E2E | 핵심 시나리오 3개 이상 |

---

# 11. 운영 고려사항

## 11.1 Docker 구성

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - db
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=stocknews
      - POSTGRES_USER=stocknews
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## 11.2 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | DB 연결 문자열 | `sqlite:///./stocknews.db` |
| `REDIS_URL` | Redis 연결 | `redis://localhost:6379` |
| `OPENAI_API_KEY` | OpenAI API 키 | (필수) |
| `DART_API_KEY` | DART 공시 API 키 | (필수) |
| `COLLECTION_INTERVAL` | 수집 주기 (분) | `5` |
| `BREAKING_THRESHOLD` | 속보 점수 임계값 | `80` |
| `CORS_ORIGINS` | 허용 Origin | `http://localhost:3000` |

## 11.3 운영 체크리스트

* 절전 모드 비활성화 (수집 서버)
* Redis 메모리 제한 설정 (`maxmemory 256mb`)
* 로그 파일 일일 롤링 (loguru 또는 logging.handlers)
* 뉴스 수집 장애 시 재시도 로직 (exponential backoff, 최대 3회)
* DB 백업 스케줄 (일 1회)
* API Rate Limiting (외부 소스 과도 호출 방지)

---

# 12. Phase 확장 로드맵

| Phase | 범위 | 핵심 산출물 |
|-------|------|-----------|
| Phase 1 | 한국 뉴스 + 공시 + 대시보드 MVP | 네이버/DART 수집, 스코어링, REST API, React 대시보드 |
| Phase 2 | 미국 뉴스 API 통합 + 분석 고도화 | Finnhub/NewsAPI, LLM 정확도 개선, 실시간 강화 |
| Phase 3 | AI 기반 뉴스 영향도 학습 모델 | 주가 상관관계 분석, 예측 모델, 예측 대시보드 |

---

# Changelog

## v1.0 (2026-02-18)

### 변경 사항

* **중복 해소**: Section 5/6의 TASK 체크박스를 제거하고 Section 9로 단일 소스화 (28건 중복 해소)
* **누락 보완**: Section 9에 17건+ 신규 TASK 추가 (환경설정, 린터, DB 마이그레이션, API 클라이언트, 타입 정의, 테스트 인프라 등)
* **스키마 일치**: Pydantic ↔ TypeScript ↔ DB 컬럼 3자 일치 수정 (sentiment enum, 필드 누락, 네이밍 통일)
* **검증 기준 강화**: Phase 2/3에 정량적 검증 기준 추가 (감성 분석 80%+, 백테스트 60%+ 등)
* **디렉토리 구조 보완**: 누락 컴포넌트 추가 (TopStockCards, MarketSelector, SentimentIndicator, NotificationBell)
* **테스트 인프라**: [13] 테스트 인프라 구축 작업 그룹 신규 추가
