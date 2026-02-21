# StockNews 개발 Task 계획서

## 전체 Phase 1/2/3 개발 작업 목록 + 병렬 처리 계획

> 참고 문서:
> - `docs/StockNews-v1.0.md` — 시스템 설계서
> - `docs/TestAgent.md` — TDD 테스트 서브에이전트 설계서

---

# 1. 실행 구조 개요

## 1.1 병렬 실행 트랙

Phase 1은 4개의 독립 트랙으로 나뉘며, 트랙 간 병렬 실행이 가능하다.

```
Wave 0: [1] 프로젝트 초기 설정 + [13] 테스트 인프라 (동시 실행)
         │
         ├── Wave 1 ──────────────────────────────────────────────┐
         │                                                         │
   ┌─────┴─────┐                                           ┌──────┴──────┐
   │  Track A   │                                           │   Track C   │
   │  Backend   │                                           │  Frontend   │
   │  Data      │                                           │             │
   └─────┬─────┘                                           └──────┬──────┘
         │                                                         │
    [2] DB 모델                                             [8] FE 프로젝트
         │                                                    설정 + 레이아웃
    ┌────┴────┐                                                    │
    │         │                                          ┌────┬────┼────┐
   [3]      [6]  ← 병렬                                [9] [10] [11] [12]
 Collector  API                                         ← 4개 병렬
    │         │
   [4]      [7]
 Processing  WS
    │
   [5]
 Scoring

   └─── Wave 2: [14] 통합 테스트 + E2E ───┘
```

## 1.2 트랙 정의

| 트랙 | 범위 | Task | 설명 |
|------|------|------|------|
| **Track 0** | 공통 | [1] + [13] | 프로젝트 초기 설정 + 테스트 인프라 |
| **Track A** | Backend 데이터 | [2] → [3] → [4] → [5] | 수집 → 분석 → 스코어링 파이프라인 |
| **Track B** | Backend API | [2] → [6] → [7] | REST API + WebSocket |
| **Track C** | Frontend | [8] → [9],[10],[11],[12] | 대시보드 + 상세 페이지 |
| **Wave 2** | 통합 | [14] | Frontend ↔ Backend 연동 + E2E |

## 1.3 병렬 처리 요약

| Wave | 동시 실행 Task | 선행 조건 | 예상 병렬도 |
|------|---------------|----------|------------|
| Wave 0 | [1-a], [1-b], [13-a], [13-b] | 없음 | 4 |
| Wave 1-A | [2] | Wave 0 완료 | 1 |
| Wave 1-B | [3] + [6] + [8] | [2] 완료 (FE는 Wave 0만) | 3 |
| Wave 1-C | [4] + [7] + [9],[10],[11],[12] | 각 선행 Task | 6 |
| Wave 1-D | [5] | [4] 완료 | 1 |
| Wave 2 | [14] | 모든 Phase 1 Task | 1 |

---

# 2. Phase 1 — MVP 세부 Task

## Wave 0: 프로젝트 초기 설정 (병렬 4)

### [1] 프로젝트 초기 설정

> 선행: 없음 | 후행: [2], [8], [13]

**병렬 분할:**

| Sub-Task | ID | 병렬 그룹 | 산출물 |
|----------|----|----------|--------|
| Backend 프로젝트 생성 | 1-a | Group A | `backend/pyproject.toml`, 의존성 |
| Frontend 프로젝트 생성 | 1-b | Group B | `frontend/package.json`, Vite 설정 |
| 공통 설정 | 1-c | Group A 후속 | Docker, `.env.example`, `.gitignore` |

**[1-a] Backend 프로젝트 초기화** (병렬 A)
- [ ] `backend/` 디렉토리 생성
- [ ] `pyproject.toml` 작성 (FastAPI, SQLAlchemy, APScheduler, pytest 등)
- [ ] Ruff 린터 설정 (`ruff.toml`)
- [ ] Backend `.env.example` 생성

**[1-b] Frontend 프로젝트 초기화** (병렬 B)
- [ ] Vite + React + TypeScript 프로젝트 생성 (`npm create vite@latest`)
- [ ] Tailwind CSS 설정 (`tailwind.config.js`, `postcss.config.js`)
- [ ] ESLint + Prettier 설정
- [ ] Frontend `.env.example` 생성

**[1-c] 공통 설정** (1-a, 1-b 완료 후)
- [ ] Docker Compose 기본 설정 (`docker-compose.yml` — Python + Redis + PostgreSQL)
- [ ] Docker Compose 개발용 오버라이드 (`docker-compose.dev.yml` — 볼륨 마운트, 핫리로드)
- [ ] `.env.development`, `.env.test`, `.env.production` 환경별 템플릿 생성
- [ ] `.gitignore` 정비 (Python, Node, IDE, 환경변수, `.env*` 제외)
- [ ] `.dockerignore` 파일 생성
- [ ] `README.md` 작성 (프로젝트 개요, 로컬 실행 방법, 테스트 방법)
- [ ] Git 브랜치 전략 정의 (`main` → `develop` → `feature/*`, `fix/*`)
- [ ] 검증: `docker-compose up` 으로 모든 서비스 기동 확인

---

### [13] 테스트 인프라 구축

> 선행: 없음 (Wave 0에서 [1]과 동시 실행) | 후행: 모든 TDD Task

**병렬 분할:**

| Sub-Task | ID | 병렬 그룹 | 산출물 |
|----------|----|----------|--------|
| Backend 테스트 인프라 | 13-a | Group A | pytest, conftest.py, factories.py |
| Frontend 테스트 인프라 | 13-b | Group B | Vitest, MSW, setup.ts |

**[13-a] Backend 테스트 설정** (병렬 A)
- [ ] pytest 설정 (`pyproject.toml [tool.pytest]`)
- [ ] pytest-cov, pytest-asyncio 설정
- [ ] `tests/conftest.py` — DB fixture, 샘플 데이터 fixture
- [ ] `tests/factories.py` — factory-boy 팩토리 (NewsEvent, ThemeStrength)
- [ ] 스모크 테스트 작성 (`tests/unit/test_smoke.py`)
- [ ] 검증: `pytest tests/unit/test_smoke.py -v` 통과

**[13-b] Frontend 테스트 설정** (병렬 B)
- [ ] Vitest 설정 (`vite.config.ts [test]`)
- [ ] `tests/setup.ts` — jsdom 환경 + RTL 설정
- [ ] `tests/mocks/server.ts` — MSW 서버
- [ ] `tests/mocks/handlers.ts` — 전체 API 엔드포인트 mock
- [ ] `tests/mocks/data.ts` — Mock 데이터
- [ ] 스모크 테스트 작성 (`tests/smoke.test.ts`)
- [ ] 검증: `npm run test -- --run` 통과

---

## Wave 1: 핵심 개발 (최대 병렬 6)

### [2] Backend: DB 모델 + 설정

> 선행: [1], [13-a] | 후행: [3], [6]
> TDD: TestAgent Section 3.2

**TDD 사이클:**

| 단계 | 작업 | 테스트 파일 |
|------|------|-----------|
| RED | 모델 + 설정 테스트 작성 | `test_models.py`, `test_config.py`, `test_database.py` |
| GREEN | 모델 + 설정 구현 | `models/`, `core/` |
| VERIFY | 커버리지 확인 | models 90%+, core 80%+ |

**Sub-Tasks:**
- [ ] RED: `tests/unit/test_models.py` — NewsEvent, ThemeStrength CRUD 테스트
- [ ] RED: `tests/unit/test_config.py` — 환경변수 로딩, 기본값 테스트
- [ ] RED: `tests/integration/test_database.py` — 테이블 생성, CRUD 테스트
- [ ] GREEN: `app/models/news_event.py` — SQLAlchemy NewsEvent 모델
- [ ] GREEN: `app/models/theme_strength.py` — SQLAlchemy ThemeStrength 모델
- [ ] GREEN: `app/core/config.py` — Pydantic Settings 환경 설정
- [ ] GREEN: `app/core/database.py` — DB 엔진 + 세션 팩토리
- [ ] GREEN: `app/core/redis.py` — Redis 연결 관리
- [ ] GREEN: `app/core/logger.py` — 로깅 설정 (loguru, 일일 롤링, 포맷 표준화)
- [ ] GREEN: Alembic 마이그레이션 초기 설정 (`alembic.ini` + `alembic/`)
- [ ] GREEN: 초기 마이그레이션 파일 생성
- [ ] GREEN: DB 시드 스크립트 (`scripts/seed.py` — 개발용 샘플 데이터)
- [ ] VERIFY: 전체 테스트 통과 + 커버리지 목표 달성

---

### [3] Backend: News Collector ← Track A

> 선행: [2] | 후행: [4]
> **[6]과 병렬 실행 가능**
> TDD: TestAgent Section 3.3

**TDD 사이클:**

| 단계 | 작업 | 테스트 파일 |
|------|------|-----------|
| RED | 수집기 + 중복제거 테스트 | `test_dedup.py`, `test_collectors.py` |
| GREEN | 수집 모듈 구현 | `collectors/`, `processing/dedup.py` |
| VERIFY | 커버리지 확인 | collectors 80%+, dedup 90%+ |

**Sub-Tasks:**
- [ ] RED: `tests/unit/test_dedup.py` — 중복 판별 로직 테스트
- [ ] RED: `tests/integration/test_collectors.py` — 네이버/DART/RSS mock 테스트
- [ ] GREEN: `app/collectors/naver.py` — 네이버 뉴스 크롤러
- [ ] GREEN: `app/collectors/dart.py` — DART 공시 API 수집
- [ ] GREEN: `app/collectors/rss.py` — RSS 피드 파서
- [ ] GREEN: `app/processing/dedup.py` — 중복 제거 로직
- [ ] GREEN: `app/collectors/scheduler.py` — APScheduler 스케줄러
- [ ] GREEN: 수집 실패 시 재시도 로직 (exponential backoff)
- [ ] VERIFY: 최소 10건 뉴스 수집 + DB 저장 확인

---

### [6] Backend: REST API 서버 ← Track B

> 선행: [2] | 후행: [7]
> **[3]과 병렬 실행 가능**
> TDD: TestAgent Section 3.6

**TDD 사이클:**

| 단계 | 작업 | 테스트 파일 |
|------|------|-----------|
| RED | API 엔드포인트 + 스키마 테스트 | `test_api_*.py`, `test_schemas.py` |
| GREEN | API + 스키마 구현 | `api/`, `schemas/` |
| VERIFY | 커버리지 확인 | api 85%+, schemas 95%+ |

**Sub-Tasks:**
- [ ] RED: `tests/unit/test_schemas.py` — SentimentEnum, NewsItem (market, source_url, published_at) 테스트
- [ ] RED: `tests/integration/test_api_news.py` — `/news/score`, `/news/top`, `/news/latest` 테스트
- [ ] RED: `tests/integration/test_api_stocks.py` — `/stocks/{code}/timeline` 테스트
- [ ] RED: `tests/integration/test_api_themes.py` — `/theme/strength` 테스트
- [ ] RED: `tests/integration/test_api_health.py` — `/health` 테스트
- [ ] GREEN: `app/schemas/common.py` — SentimentEnum, TimelinePoint, HealthResponse
- [ ] GREEN: `app/schemas/news.py` — NewsScoreResponse, NewsItem, NewsListResponse, etc.
- [ ] GREEN: `app/schemas/theme.py` — ThemeItem, ThemeStrengthResponse
- [ ] GREEN: `app/main.py` — FastAPI 앱 + CORS + 에러 핸들링 미들웨어
- [ ] GREEN: `app/api/router.py` — 라우터 통합 (API 버저닝: `/api/v1/` prefix)
- [ ] GREEN: `app/api/news.py` — /news/* 엔드포인트 (score, top, latest)
- [ ] GREEN: `app/api/themes.py` — /theme/* 엔드포인트
- [ ] GREEN: `app/api/stocks.py` — /stocks/* 엔드포인트
- [ ] GREEN: `app/api/health.py` — /health 엔드포인트
- [ ] GREEN: API Rate Limiting 미들웨어 (외부 소스 과도 호출 방지)
- [ ] GREEN: Swagger 메타데이터 설정 (title, description, version)
- [ ] RED: `tests/integration/test_cors.py` — CORS 허용/차단 테스트
- [ ] VERIFY: Swagger UI 정상 + 전체 테스트 통과

---

### [8] Frontend: 프로젝트 설정 + 레이아웃 ← Track C

> 선행: [1-b], [13-b] | 후행: [9], [10], [11], [12]
> **[2], [3]과 병렬 실행 가능** (MSW mock 사용으로 Backend 없이 개발 가능)
> **참고**: TypeScript 타입은 [6]의 Pydantic 스키마와 일치시켜야 하므로, API 스키마 합의가 선행 필요 (v1.0 Section 7 기준)
> TDD: TestAgent Section 3.8

**TDD 사이클:**

| 단계 | 작업 | 테스트 파일 |
|------|------|-----------|
| RED | API 클라이언트 + 공통 컴포넌트 테스트 | `api/*.test.ts`, `Loading.test.tsx` |
| GREEN | 클라이언트 + 컴포넌트 구현 | `api/`, `types/`, `components/common/` |
| VERIFY | 커버리지 확인 | api 80%+, common 80%+ |

**Sub-Tasks (병렬 2그룹):**

*Group A — API + 타입:*
- [ ] RED: `tests/api/client.test.ts` — 베이스 URL, 에러 핸들링
- [ ] RED: `tests/api/news.test.ts` — fetchTopNews, fetchLatestNews, fetchNewsScore
- [ ] RED: `tests/api/themes.test.ts` — fetchThemeStrength
- [ ] RED: `tests/api/stocks.test.ts` — fetchStockTimeline
- [ ] GREEN: `src/types/news.ts` — Sentiment, NewsScore, NewsItem, TimelinePoint, StockTimeline
- [ ] GREEN: `src/types/theme.ts` — ThemeItem
- [ ] GREEN: `src/types/api.ts` — PaginatedResponse, WebSocketMessage
- [ ] GREEN: `src/api/client.ts` — API 클라이언트 인스턴스
- [ ] GREEN: `src/api/news.ts`, `themes.ts`, `stocks.ts` — API 함수

*Group B — UI 프레임 + 공통:*
- [ ] RED: `tests/components/Loading.test.tsx` — 스피너 렌더링
- [ ] RED: `tests/components/ErrorBoundary.test.tsx` — fallback UI
- [ ] GREEN: `src/utils/format.ts` — 날짜/숫자 포맷팅
- [ ] GREEN: `src/utils/constants.ts` — API URL, 상수
- [ ] GREEN: React Router 라우팅 구성 (`src/App.tsx`)
- [ ] GREEN: TanStack Query Provider 설정
- [ ] GREEN: `src/components/layout/Header.tsx`, `Sidebar.tsx`, `Layout.tsx`
- [ ] GREEN: `src/components/common/Loading.tsx`, `ErrorBoundary.tsx`
- [ ] VERIFY: `npm run dev` 빈 대시보드 렌더링 + 테스트 통과

---

### [4] Backend: News Processing ← Track A (계속)

> 선행: [3] | 후행: [5]
> **[7]과 병렬 실행 가능**
> TDD: TestAgent Section 3.4

**Sub-Tasks:**
- [ ] RED: `tests/unit/test_stock_mapper.py` — 종목 매핑 테스트 (KOSPI 200, 90%+ 정확도)
- [ ] RED: `tests/unit/test_theme_classifier.py` — 테마 분류 테스트
- [ ] RED: `tests/unit/test_sentiment.py` — 감성 분석 테스트 + OpenAI 실패 fallback
- [ ] GREEN: `app/processing/stock_mapper.py` — 종목명↔코드 매핑 사전 + 로직
- [ ] GREEN: `app/processing/theme_classifier.py` — 키워드 기반 테마 분류
- [ ] GREEN: `app/processing/sentiment.py` — LLM 기반 감성 분석
- [ ] VERIFY: 커버리지 processing/ 85%+, KOSPI 200 매핑 90%+

---

### [7] Backend: Redis Pub/Sub + WebSocket ← Track B (계속)

> 선행: [6] | 후행: [14]
> **[4]와 병렬 실행 가능**
> TDD: TestAgent Section 3.7

**Sub-Tasks:**
- [ ] RED: `tests/integration/test_redis_pubsub.py` — 발행/구독, 임계값 판정
- [ ] RED: `tests/integration/test_websocket.py` — 연결, 메시지 수신, ping/pong, 타임아웃, 최대 연결 수
- [ ] GREEN: Redis Pub/Sub 발행/구독 로직 (`app/core/redis.py` 확장)
- [ ] GREEN: 속보 판정 로직 (score >= 80)
- [ ] GREEN: WebSocket 엔드포인트 (`app/api/news.py` WS 추가)
- [ ] GREEN: Heartbeat (ping/pong) 프로토콜
- [ ] VERIFY: WebSocket 이벤트 수신 테스트 통과

---

### [9] Frontend: 대시보드 페이지 ← Track C (계속)

> 선행: [8] | 후행: [14]
> **[10], [11], [12]와 병렬 실행 가능**
> TDD: TestAgent Section 3.9

**Sub-Tasks:**
- [ ] RED: `tests/pages/DashboardPage.test.tsx` — Top 종목, 뉴스 피드, 테마 차트
- [ ] RED: `tests/components/TopStockCards.test.tsx` — 종목 카드 렌더링
- [ ] RED: `tests/components/NewsCard.test.tsx` — 뉴스 카드 (published_at, sentiment 배지)
- [ ] RED: `tests/components/MarketSelector.test.tsx` — KR/US 탭
- [ ] RED: `tests/hooks/useTopNews.test.ts` — 데이터 fetch, 자동 새로고침
- [ ] GREEN: `src/pages/DashboardPage.tsx`
- [ ] GREEN: `src/components/news/TopStockCards.tsx`
- [ ] GREEN: `src/components/news/NewsList.tsx`, `NewsCard.tsx`, `NewsScoreBadge.tsx`
- [ ] GREEN: `src/components/common/MarketSelector.tsx`
- [ ] GREEN: `src/components/charts/ThemeStrengthChart.tsx`
- [ ] GREEN: `src/hooks/useTopNews.ts`
- [ ] VERIFY: API 연동 대시보드 정상 렌더링 + 테스트 통과

---

### [10] Frontend: 종목 상세 페이지

> 선행: [8] | 후행: [14]
> **[9], [11], [12]와 병렬 실행 가능**
> TDD: TestAgent Section 3.10

**Sub-Tasks:**
- [ ] RED: `tests/pages/StockDetailPage.test.tsx` — URL 파라미터, 에러 처리
- [ ] RED: `tests/components/ScoreTimeline.test.tsx` — 7일 차트
- [ ] RED: `tests/components/SentimentPie.test.tsx` — 감성 분포
- [ ] RED: `tests/hooks/useNewsScore.test.ts` — 스코어 + 타임라인 fetch
- [ ] GREEN: `src/pages/StockDetailPage.tsx`
- [ ] GREEN: `src/components/charts/ScoreTimeline.tsx`
- [ ] GREEN: `src/components/charts/SentimentPie.tsx`
- [ ] GREEN: `src/hooks/useNewsScore.ts`
- [ ] VERIFY: `/stocks/005930` 접근 시 데이터 표시 + 테스트 통과

---

### [11] Frontend: 테마 분석 페이지

> 선행: [8] | 후행: [14]
> **[9], [10], [12]와 병렬 실행 가능**
> TDD: TestAgent Section 3.11

**Sub-Tasks:**
- [ ] RED: `tests/pages/ThemeAnalysisPage.test.tsx` — 차트, 종목 목록
- [ ] RED: `tests/components/ThemeStrengthChart.test.tsx` — 바 차트
- [ ] RED: `tests/components/SentimentIndicator.test.tsx` — 감성 배지
- [ ] RED: `tests/hooks/useThemeStrength.test.ts`
- [ ] GREEN: `src/pages/ThemeAnalysisPage.tsx`
- [ ] GREEN: `src/components/charts/ThemeStrengthChart.tsx` (재사용)
- [ ] GREEN: `src/components/common/SentimentIndicator.tsx`
- [ ] GREEN: `src/hooks/useThemeStrength.ts`
- [ ] VERIFY: 테마 차트 렌더링 + 클릭 연동 + 테스트 통과

---

### [12] Frontend: 실시간 알림

> 선행: [8] | 후행: [14]
> **[9], [10], [11]과 병렬 실행 가능**
> TDD: TestAgent Section 3.12

**Sub-Tasks:**
- [ ] RED: `tests/hooks/useWebSocket.test.ts` — 연결, 메시지, 재연결, ping/pong
- [ ] RED: `tests/components/Toast.test.tsx` — 표시, 자동 사라짐
- [ ] RED: `tests/components/NotificationBell.test.tsx` — 배지, 드롭다운
- [ ] GREEN: `src/hooks/useWebSocket.ts`
- [ ] GREEN: `src/components/common/Toast.tsx`
- [ ] GREEN: `src/components/common/NotificationBell.tsx`
- [ ] VERIFY: 속보 이벤트 → 토스트 표시 + 테스트 통과

---

### [5] Backend: Scoring Engine ← Track A (최종)

> 선행: [4] | 후행: [14]
> TDD: TestAgent Section 3.5

**Sub-Tasks:**
- [ ] RED: `tests/unit/test_scoring.py` — Recency, Frequency, Sentiment, Disclosure, 가중합
- [ ] RED: `tests/unit/test_aggregator.py` — 종목별/테마별 집계
- [ ] GREEN: `app/scoring/engine.py` — 점수 계산 (4요소 가중합)
- [ ] GREEN: Disclosure Bonus 판정 로직
- [ ] GREEN: `app/scoring/aggregator.py` — 종목별 집계 + 테마 강도
- [ ] VERIFY: 커버리지 scoring/ 90%+ + 시나리오 테스트 통과

---

## Wave 2: 통합 + E2E

### [14] Frontend ↔ Backend 통합 + E2E 테스트

> 선행: [5], [6], [7], [9], [10], [11], [12] 모두 완료 | 후행: Phase 2

**Sub-Tasks:**
- [ ] Playwright 설정 (`frontend/playwright.config.ts`)
- [ ] Frontend API 클라이언트를 실제 Backend URL로 연결
- [ ] CORS 설정 검증 (Frontend → Backend 통신)
- [ ] 전체 데이터 파이프라인 E2E 확인: 뉴스 수집 → 분석 → 스코어링 → API → 대시보드
- [ ] WebSocket 실시간 알림 E2E 확인: Redis 발행 → WS → 토스트
- [ ] CI/CD 파이프라인 생성 (`.github/workflows/test.yml`)
- [ ] Playwright E2E 테스트:
  - [ ] 대시보드 → 종목 클릭 → 상세 페이지 이동
  - [ ] 테마 분석 → 테마 클릭 → 종목 목록 표시
  - [ ] 속보 알림 수신 확인
- [ ] 전체 테스트 스위트 최종 실행:
  - [ ] Backend: `pytest --cov=app --cov-fail-under=80`
  - [ ] Frontend: `npm run test -- --run --coverage`
- [ ] 검증: 모든 테스트 통과 + 커버리지 목표 달성

---

# 3. Phase 1 병렬 실행 타임라인

```
시간 →  ────────────────────────────────────────────────────────────→

Wave 0  ┌─────────────────┐
        │ [1-a] BE 설정    │
        │ [1-b] FE 설정    │  ← 병렬 2
        │ [13-a] BE 테스트  │
        │ [13-b] FE 테스트  │  ← 병렬 2
        └────────┬────────┘
                 │
Wave 1  ┌────────┴────────┐
        │    [2] DB 모델   │
        └──┬──────────┬───┘
           │          │
        ┌──┴──┐   ┌──┴──┐   ┌──────────────┐
        │ [3] │   │ [6] │   │ [8] FE 설정   │  ← 병렬 3
        │Coll.│   │ API │   └──┬──┬──┬──┬──┘
        └──┬──┘   └──┬──┘      │  │  │  │
        ┌──┴──┐   ┌──┴──┐   ┌──┴┐┌┴─┐┌┴─┐┌┴──┐
        │ [4] │   │ [7] │   │[9]││10││11││[12]│  ← 병렬 6
        │Proc.│   │ WS  │   │   ││  ││  ││   │
        └──┬──┘   └─────┘   └───┘└──┘└──┘└───┘
        ┌──┴──┐
        │ [5] │
        │Score│
        └─────┘
                 │
Wave 2  ┌────────┴────────┐
        │  [14] 통합+E2E  │
        └─────────────────┘
```

**최대 동시 실행: 6 Task** (Wave 1-C: [4] + [7] + [9] + [10] + [11] + [12])

---

# 4. Phase 2 — 분석 고도화

> 선행: Phase 1 완료

## Task 목록

### [P2-1] LLM 프롬프트 튜닝

> **[P2-2]와 병렬 실행 가능**

- [ ] RED: `tests/unit/test_sentiment_accuracy.py` — 100건 샘플 80%+ 정확도 테스트
- [ ] 수동 라벨링 데이터셋 100건 구축 (positive/neutral/negative)
- [ ] 프롬프트 개선 + 파라미터 조정
- [ ] VERIFY: 정확도 80%+ 테스트 통과

### [P2-2] 뉴스 요약 기능

> **[P2-1]과 병렬 실행 가능**

- [ ] RED: `tests/unit/test_summary.py` — 요약 길이, 핵심 정보 포함
- [ ] LLM 요약 파이프라인 구현 (`app/processing/summary.py`)
- [ ] DB 스키마: `news_event.summary` 필드 활용
- [ ] VERIFY: 수동 검증 20건 — 핵심 정보 포함율 80%+

### [P2-3] 미국 뉴스 소스 연동

> **[P2-1], [P2-2]와 병렬 실행 가능**

- [ ] RED: `tests/integration/test_us_collectors.py` — Finnhub/NewsAPI mock 테스트
- [ ] `app/collectors/finnhub.py` — Finnhub News API 수집기
- [ ] `app/collectors/newsapi.py` — NewsAPI 수집기
- [ ] 영문 종목 매핑 (ticker → 종목명)
- [ ] VERIFY: 일 10건+ 미국 뉴스 수집 테스트 통과

### [P2-4] 실시간 수집 주기 단축

> [P2-3] 완료 후

- [ ] RED: `tests/integration/test_scheduler_performance.py` — 1분 주기 수집 지속 가능성 테스트
- [ ] APScheduler 주기 조정 (5분 → 1분)
- [ ] 부하 테스트 (1분 주기 지속 가능성, 메모리/CPU 사용량)
- [ ] VERIFY: 1분 이내 수집 주기 달성 + 성능 테스트 통과

### [P2-5] Frontend 차트 인터랙션 강화

> **[P2-1]~[P2-3]과 병렬 실행 가능**

- [ ] RED: `tests/components/ChartDrilldown.test.tsx` — 차트 포인트 클릭 → 뉴스 목록 표시
- [ ] RED: `tests/components/FilterPanel.test.tsx` — 날짜/감성/테마 필터 동작
- [ ] GREEN: 드릴다운: 차트 포인트 클릭 → 해당 일자 뉴스 목록
- [ ] GREEN: 필터: 날짜 범위, 감성, 테마 필터 UI
- [ ] VERIFY: 필터 적용 시 데이터 갱신 확인 + 테스트 통과

### Phase 2 병렬 구조

```
┌────────────────────────────────────────┐
│  [P2-1] LLM 튜닝                       │
│  [P2-2] 뉴스 요약   ← 3개 병렬         │
│  [P2-3] 미국 뉴스                      │
│  [P2-5] FE 차트 강화 ← FE 독립 병렬    │
└──────────────┬─────────────────────────┘
               │
        [P2-4] 수집 주기 단축
```

### Phase 2 검증 기준

- [ ] 감성 분석 정확도: 100건 샘플 중 80%+ 일치
- [ ] 미국 뉴스: 일 10건+ 수집 정상 동작
- [ ] 뉴스 요약: 20건 수동 검증 핵심 정보 포함
- [ ] 수집 주기: 1분 이내 달성
- [ ] 전체 커버리지 유지: Backend 80%+, Frontend 70%+

---

# 5. Phase 3 — AI 학습 모델

> 선행: Phase 2 완료

## Task 목록

### [P3-1] 상관관계 데이터 수집

> **[P3-2]의 선행 조건**

- [ ] 뉴스 이벤트 ↔ 주가 변동 데이터 매칭 파이프라인
- [ ] 주가 데이터 수집 모듈 (한국투자증권 API 또는 Yahoo Finance)
- [ ] 6개월+ 히스토리컬 데이터 축적
- [ ] RED: `tests/unit/test_data_alignment.py` — 뉴스↔주가 시간 정렬 검증
- [ ] VERIFY: 데이터 정합성 검증 (뉴스 시각 ↔ 주가 시간 정렬)

### [P3-2] AI 예측 모델 구축

> 선행: [P3-1]

- [ ] RED: `tests/unit/test_prediction.py` — 백테스트 60%+, 상관계수 0.3+
- [ ] 뉴스 피처 엔지니어링 (스코어, 감성, 빈도 → 피처 벡터)
- [ ] 모델 학습 (Random Forest → LSTM/Transformer 순차 고도화)
- [ ] VERIFY: 백테스트 정확도 60%+, 상관계수 0.3+

### [P3-3] 예측 점수 API

> 선행: [P3-2]
> **[P3-4]와 병렬 실행 가능**

- [ ] RED: `tests/integration/test_api_prediction.py` — 예측 점수 엔드포인트 요청/응답 테스트
- [ ] RED: `tests/unit/test_prediction_schema.py` — PredictionResponse 스키마 검증
- [ ] GREEN: `GET /news/prediction?stock={code}` 엔드포인트
- [ ] GREEN: Pydantic 스키마 (`schemas/prediction.py`) + TypeScript 타입 추가
- [ ] VERIFY: API 응답 정확성 + 스키마 일치 + 테스트 통과

### [P3-4] 대시보드 예측 뷰

> 선행: [P3-2]
> **[P3-3]과 병렬 실행 가능**

- [ ] RED: `tests/components/PredictionChart.test.tsx` — 예측 차트 렌더링
- [ ] RED: `tests/components/PredictionSignal.test.tsx` — 신호등 표시 (상승/하락/중립)
- [ ] RED: `tests/hooks/usePrediction.test.ts` — 예측 데이터 fetch
- [ ] GREEN: 예측 점수 시각화 (차트 + 신호등 표시)
- [ ] GREEN: 대시보드에 예측 탭 추가
- [ ] GREEN: `src/hooks/usePrediction.ts`
- [ ] VERIFY: 예측 데이터 렌더링 테스트 통과

### Phase 3 병렬 구조

```
[P3-1] 데이터 수집  (순차)
    │
[P3-2] 모델 구축    (순차)
    │
    ├── [P3-3] 예측 API       ← 병렬 2
    └── [P3-4] 대시보드 뷰
```

### Phase 3 검증 기준

- [ ] 학습 데이터 6개월+ 축적
- [ ] 백테스트 정확도 60%+ (1일 주가 방향 예측)
- [ ] 상관계수 0.3+
- [ ] 대시보드 예측 뷰 정상 렌더링

---

# 6. 전체 Task 요약표

## Phase 1 (총 15개 Task, 103개+ 체크박스)

| ID | Task | 선행 | 병렬 가능 대상 | TDD 참조 |
|----|------|------|--------------|----------|
| 1-a | Backend 프로젝트 초기화 | - | 1-b, 13-a, 13-b | - |
| 1-b | Frontend 프로젝트 초기화 | - | 1-a, 13-a, 13-b | - |
| 1-c | 공통 설정 (Docker 등) | 1-a, 1-b | - | - |
| 13-a | Backend 테스트 인프라 | - | 1-a, 1-b, 13-b | TestAgent 3.1 |
| 13-b | Frontend 테스트 인프라 | - | 1-a, 1-b, 13-a | TestAgent 3.1 |
| 2 | DB 모델 + 설정 | 1, 13-a | - | TestAgent 3.2 |
| 3 | News Collector | 2 | **6, 8** | TestAgent 3.3 |
| 6 | REST API 서버 | 2 | **3, 8** | TestAgent 3.6 |
| 8 | FE 프로젝트 설정 | 1-b, 13-b, 스키마 합의 | **3** | TestAgent 3.8 |
| 4 | News Processing | 3 | **7, 9, 10, 11, 12** | TestAgent 3.4 |
| 7 | Redis + WebSocket | 6 | **4, 9, 10, 11, 12** | TestAgent 3.7 |
| 5 | Scoring Engine | 4 | - | TestAgent 3.5 |
| 9 | FE 대시보드 | 8 | **10, 11, 12** | TestAgent 3.9 |
| 10 | FE 종목 상세 | 8 | **9, 11, 12** | TestAgent 3.10 |
| 11 | FE 테마 분석 | 8 | **9, 10, 12** | TestAgent 3.11 |
| 12 | FE 실시간 알림 | 8 | **9, 10, 11** | TestAgent 3.12 |
| 14 | 통합 + E2E + CI/CD | 전체 (5,6,7,9,10,11,12) | - | TestAgent 8 |

## Phase 2 (총 5개 Task)

| ID | Task | 병렬 가능 대상 |
|----|------|--------------|
| P2-1 | LLM 프롬프트 튜닝 | **P2-2, P2-3, P2-5** |
| P2-2 | 뉴스 요약 | **P2-1, P2-3, P2-5** |
| P2-3 | 미국 뉴스 연동 | **P2-1, P2-2, P2-5** |
| P2-4 | 수집 주기 단축 | - (P2-3 후) |
| P2-5 | FE 차트 강화 | **P2-1, P2-2, P2-3** |

## Phase 3 (총 4개 Task)

| ID | Task | 병렬 가능 대상 |
|----|------|--------------|
| P3-1 | 상관관계 데이터 수집 | - |
| P3-2 | AI 예측 모델 구축 | - (P3-1 후) |
| P3-3 | 예측 점수 API | **P3-4** |
| P3-4 | 대시보드 예측 뷰 | **P3-3** |

---

# 7. 에이전트 배정 가이드

각 Task 실행 시 권장 에이전트 배정:

| Task 유형 | TDD RED (테스트) | GREEN (구현) | VERIFY (검증) |
|----------|-----------------|-------------|-------------|
| Backend 단위 테스트 | `tdd-guide` (sonnet) | `executor` (sonnet) | `tdd-guide` (sonnet) |
| Backend 통합 테스트 | `tdd-guide` (sonnet) | `executor` (sonnet) | `qa-tester` (sonnet) |
| Frontend 컴포넌트 | `tdd-guide` (sonnet) | `designer` (sonnet) | `tdd-guide` (sonnet) |
| Frontend 페이지 | `tdd-guide` (sonnet) | `designer` (sonnet) | `qa-tester` (sonnet) |
| API 설계/리뷰 | `architect` (opus) | `executor` (sonnet) | `code-reviewer` (opus) |
| E2E 테스트 | `qa-tester-high` (opus) | - | `qa-tester-high` (opus) |
| 인프라/설정 | - | `executor-low` (haiku) | `build-fixer-low` (haiku) |

---

# 8. 실행 커맨드 레퍼런스

```bash
# Backend 테스트
cd backend
pytest tests/unit -v -m unit                    # 단위 테스트만
pytest tests/integration -v -m integration       # 통합 테스트만
pytest tests/ -v --cov=app --cov-report=term-missing  # 전체 + 커버리지
pytest tests/ --cov=app --cov-fail-under=80     # 커버리지 80% 미달 시 실패

# Frontend 테스트
cd frontend
npm run test -- --run                           # 전체 테스트
npm run test -- --run --coverage                # 커버리지 포함
npm run test -- tests/components/               # 컴포넌트만
npm run test -- tests/hooks/                    # 훅만

# E2E 테스트
cd frontend
npx playwright test                             # Playwright E2E

# 린터
cd backend && ruff check .                      # Python 린트
cd frontend && npx eslint src/                  # TypeScript 린트

# Docker
docker-compose up -d                            # 서비스 기동
docker-compose down                             # 서비스 중지
```
