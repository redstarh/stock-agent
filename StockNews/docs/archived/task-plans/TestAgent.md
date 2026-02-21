# TestAgent — TDD 기반 테스트 서브에이전트 설계서

## StockNews 프로젝트 전체 개발 단계별 TDD 테스트 계획

---

# 1. TestAgent 개요

## 1.1 목적

StockNews 프로젝트의 모든 개발 단계에서 **TDD(Test-Driven Development)** 원칙을 강제하는 독립적인 Test SubAgent를 정의한다. 개발 에이전트(executor)가 코드를 작성하기 **전에** TestAgent가 먼저 테스트를 작성하고, 구현 후 검증까지 수행한다.

## 1.2 TDD 사이클

```
┌──────────────────────────────────────────────────┐
│                  TDD 사이클                        │
│                                                    │
│   RED ──→ GREEN ──→ REFACTOR ──→ VERIFY           │
│    │         │          │           │              │
│  테스트    최소 구현   코드 개선   커버리지 확인     │
│  작성      (통과)     (통과 유지)  (80%+)          │
│  (실패)                                            │
└──────────────────────────────────────────────────┘
```

| 단계 | 수행 주체 | 설명 |
|------|----------|------|
| **RED** | TestAgent | 실패하는 테스트 작성 |
| **GREEN** | Executor Agent | 테스트를 통과시키는 최소 코드 구현 |
| **REFACTOR** | Executor Agent | 코드 품질 개선 (테스트 통과 유지) |
| **VERIFY** | TestAgent | 전체 테스트 통과 + 커버리지 확인 |

## 1.3 TestAgent 호출 규칙

```
개발 Task 시작 시:
  1. TestAgent가 해당 Task의 테스트를 먼저 작성 (RED)
  2. Executor Agent가 구현 (GREEN)
  3. Executor Agent가 리팩터링 (REFACTOR)
  4. TestAgent가 검증 (VERIFY)
  5. 통과 시 → 다음 Task로 이동
  6. 실패 시 → 2번으로 돌아가 수정
```

---

# 2. 테스트 인프라

## 2.1 Backend 테스트 스택

| 도구 | 용도 | 설정 파일 |
|------|------|----------|
| pytest | 테스트 프레임워크 | `backend/pyproject.toml` |
| pytest-cov | 커버리지 측정 | `backend/pyproject.toml` |
| pytest-asyncio | 비동기 테스트 | `backend/pyproject.toml` |
| httpx | FastAPI TestClient 대안 | `backend/pyproject.toml` |
| factory-boy | 테스트 데이터 팩토리 | `backend/pyproject.toml` |
| respx / responses | HTTP mock | `backend/pyproject.toml` |
| fakeredis | Redis mock | `backend/pyproject.toml` |

### pytest 설정

```toml
# backend/pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short --strict-markers"
markers = [
    "unit: 단위 테스트",
    "integration: 통합 테스트",
    "slow: 느린 테스트 (외부 API)",
]

[tool.coverage.run]
source = ["app"]
omit = ["tests/*", "alembic/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### conftest.py Fixture 체계

```python
# backend/tests/conftest.py

@pytest.fixture
def db_engine():
    """SQLite in-memory 엔진"""

@pytest.fixture
def db_session(db_engine):
    """트랜잭션 격리된 DB 세션 (각 테스트 후 rollback)"""

@pytest.fixture
def async_client(db_session):
    """FastAPI TestClient (httpx.AsyncClient)"""

@pytest.fixture
def sample_news_events(db_session):
    """테스트용 뉴스 이벤트 5건 (다양한 종목/테마/감성)"""

@pytest.fixture
def sample_theme_strength(db_session):
    """테스트용 테마 강도 데이터"""

@pytest.fixture
def mock_naver_response():
    """네이버 뉴스 크롤링 mock HTML 응답"""

@pytest.fixture
def mock_dart_response():
    """DART API mock JSON 응답"""

@pytest.fixture
def mock_rss_feed():
    """RSS 피드 mock XML 응답"""

@pytest.fixture
def fake_redis():
    """fakeredis 인스턴스"""

@pytest.fixture
def mock_openai():
    """OpenAI API mock (감성 분석 응답)"""
```

## 2.2 Frontend 테스트 스택

| 도구 | 용도 | 설정 파일 |
|------|------|----------|
| Vitest | 테스트 프레임워크 | `frontend/vite.config.ts` |
| React Testing Library | 컴포넌트 테스트 | `frontend/tests/setup.ts` |
| MSW (Mock Service Worker) | API mocking | `frontend/tests/mocks/` |
| @testing-library/user-event | 사용자 인터랙션 시뮬레이션 | - |
| Playwright | E2E 테스트 | `frontend/playwright.config.ts` |

### Vitest 설정

```typescript
// frontend/vite.config.ts
export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.d.ts', 'src/main.tsx'],
      thresholds: {
        statements: 70,
        branches: 70,
        functions: 70,
        lines: 70,
      },
    },
  },
});
```

### MSW 핸들러 체계

```typescript
// frontend/tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';
import { mockNewsTop, mockNewsLatest, mockThemeStrength, mockStockTimeline } from './data';

export const handlers = [
  http.get('/api/news/top', ({ request }) => {
    const url = new URL(request.url);
    const market = url.searchParams.get('market') || 'KR';
    return HttpResponse.json(mockNewsTop(market));
  }),
  http.get('/api/news/latest', () => HttpResponse.json(mockNewsLatest())),
  http.get('/api/news/score', () => HttpResponse.json(mockNewsScore())),
  http.get('/api/stocks/:code/timeline', ({ params }) =>
    HttpResponse.json(mockStockTimeline(params.code as string))
  ),
  http.get('/api/theme/strength', () => HttpResponse.json(mockThemeStrength())),
  http.get('/api/health', () => HttpResponse.json({ status: 'ok', version: '1.0.0' })),
];
```

## 2.3 테스트 디렉토리 구조

```
backend/tests/
├── conftest.py                  # 공통 fixture
├── factories.py                 # factory-boy 팩토리
├── unit/
│   ├── test_scoring.py          # Scoring Engine
│   ├── test_stock_mapper.py     # 종목 매핑
│   ├── test_dedup.py            # 중복 제거
│   ├── test_theme_classifier.py # 테마 분류
│   ├── test_sentiment.py        # 감성 분석
│   ├── test_recency.py          # Recency 시간 감쇠
│   └── test_aggregator.py       # 집계 로직
├── integration/
│   ├── test_api_news.py         # /news/* 엔드포인트
│   ├── test_api_themes.py       # /theme/* 엔드포인트
│   ├── test_api_stocks.py       # /stocks/* 엔드포인트
│   ├── test_api_health.py       # /health 엔드포인트
│   ├── test_collectors.py       # 수집기 (mock)
│   ├── test_database.py         # DB CRUD
│   ├── test_websocket.py        # WebSocket
│   └── test_redis_pubsub.py     # Redis Pub/Sub
└── e2e/                         # (Phase 1 이후)

frontend/tests/
├── setup.ts                     # 테스트 환경 설정
├── mocks/
│   ├── handlers.ts              # MSW 핸들러
│   ├── server.ts                # MSW 서버 설정
│   └── data.ts                  # Mock 데이터
├── components/
│   ├── NewsCard.test.tsx
│   ├── NewsList.test.tsx
│   ├── TopStockCards.test.tsx
│   ├── ScoreTimeline.test.tsx
│   ├── SentimentPie.test.tsx
│   ├── ThemeStrengthChart.test.tsx
│   ├── MarketSelector.test.tsx
│   ├── SentimentIndicator.test.tsx
│   ├── NotificationBell.test.tsx
│   ├── Toast.test.tsx
│   ├── Loading.test.tsx
│   └── ErrorBoundary.test.tsx
├── pages/
│   ├── DashboardPage.test.tsx
│   ├── StockDetailPage.test.tsx
│   └── ThemeAnalysisPage.test.tsx
├── hooks/
│   ├── useNewsScore.test.ts
│   ├── useTopNews.test.ts
│   ├── useThemeStrength.test.ts
│   └── useWebSocket.test.ts
└── api/
    ├── client.test.ts
    ├── news.test.ts
    ├── themes.test.ts
    └── stocks.test.ts
```

---

# 3. Phase 1 — Task별 TDD 계획

## 3.0 TDD 실행 순서 개요

```
[13] 테스트 인프라 구축     ← 가장 먼저 실행 (다른 모든 Task의 선행 조건)
 │
 ├──→ [2] DB 모델 테스트 → 구현
 │     │
 │     ├──→ [3] Collector 테스트 → 구현
 │     │     │
 │     │     └──→ [4] Processing 테스트 → 구현
 │     │           │
 │     │           └──→ [5] Scoring 테스트 → 구현
 │     │
 │     └──→ [6] REST API 테스트 → 구현
 │           │
 │           └──→ [7] WebSocket 테스트 → 구현
 │
 └──→ [8] Frontend 설정 + 테스트 환경
       │
       ├──→ [9] 대시보드 테스트 → 구현
       ├──→ [10] 종목 상세 테스트 → 구현
       ├──→ [11] 테마 분석 테스트 → 구현
       └──→ [12] 실시간 알림 테스트 → 구현
```

**핵심**: Task [13]이 [1]과 동시에 시작되어, 다른 모든 Task보다 먼저 완료되어야 함.

---

## 3.1 [13] 테스트 인프라 구축

> **이 Task는 모든 TDD의 기반이므로 가장 먼저 실행**

### RED 단계 — 스모크 테스트 작성

```python
# backend/tests/unit/test_smoke.py
def test_import_app():
    """FastAPI 앱 import가 에러 없이 성공하는지 확인"""
    from app.main import app
    assert app is not None

def test_db_connection(db_session):
    """DB 세션이 정상 생성되는지 확인"""
    assert db_session is not None
```

```typescript
// frontend/tests/smoke.test.ts
import { render, screen } from '@testing-library/react';
import App from '../src/App';

test('App renders without crashing', () => {
  render(<App />);
  expect(screen.getByRole('main')).toBeInTheDocument();
});
```

### GREEN 단계 — 인프라 구현

| 항목 | 파일 | 완료 기준 |
|------|------|----------|
| pytest + conftest.py | `tests/conftest.py` | `pytest` 실행 시 에러 없음 |
| factory-boy 팩토리 | `tests/factories.py` | NewsEvent, ThemeStrength 팩토리 정의 |
| Vitest 설정 | `vite.config.ts` | `npm run test` 실행 시 에러 없음 |
| MSW 서버 | `tests/mocks/server.ts` | API mock 응답 반환 |
| Mock 데이터 | `tests/mocks/data.ts` | 전체 API 응답 mock 데이터 |

### VERIFY

```bash
# Backend
cd backend && pytest tests/ -v --tb=short
# Frontend
cd frontend && npm run test -- --run
```

---

## 3.2 [2] Backend: DB 모델 + 설정

### RED — 테스트 먼저 작성

```python
# tests/unit/test_models.py
class TestNewsEventModel:
    def test_create_news_event(self, db_session):
        """news_event 레코드 생성 및 필드 검증"""
        event = NewsEvent(
            market="KR", stock_code="005930", stock_name="삼성전자",
            title="테스트 뉴스", sentiment="positive", source="naver",
        )
        db_session.add(event)
        db_session.commit()
        assert event.id is not None
        assert event.created_at is not None

    def test_news_event_sentiment_enum(self, db_session):
        """sentiment 필드가 positive/neutral/negative만 허용"""
        # 유효한 값
        for s in ["positive", "neutral", "negative"]:
            event = NewsEvent(market="KR", stock_code="005930",
                              title="test", sentiment=s, source="naver")
            db_session.add(event)
        db_session.commit()

    def test_news_event_dedup_index(self, db_session):
        """source_url 중복 시 IntegrityError 발생"""
        ...

    def test_news_event_default_values(self, db_session):
        """기본값 검증: sentiment='neutral', news_score=0, is_disclosure=False"""
        ...

class TestThemeStrengthModel:
    def test_create_theme_strength(self, db_session):
        """theme_strength 레코드 생성"""
        ...

    def test_theme_unique_constraint(self, db_session):
        """(date, market, theme) 유니크 제약 검증"""
        ...

# tests/unit/test_config.py
class TestConfig:
    def test_default_database_url(self):
        """기본 DATABASE_URL이 sqlite"""
        ...

    def test_required_env_vars(self):
        """필수 환경변수 누락 시 ValidationError"""
        ...

# tests/integration/test_database.py
class TestDatabaseConnection:
    def test_create_tables(self, db_engine):
        """모든 테이블 생성 확인"""
        ...

    def test_crud_news_event(self, db_session):
        """news_event CRUD 동작"""
        ...

    def test_crud_theme_strength(self, db_session):
        """theme_strength CRUD 동작"""
        ...
```

### GREEN — 구현 대상

| 파일 | 내용 |
|------|------|
| `app/models/news_event.py` | SQLAlchemy NewsEvent 모델 |
| `app/models/theme_strength.py` | SQLAlchemy ThemeStrength 모델 |
| `app/core/config.py` | Pydantic Settings 기반 환경 설정 |
| `app/core/database.py` | DB 엔진 + 세션 팩토리 |
| `app/core/redis.py` | Redis 연결 관리 |
| `alembic/` | 초기 마이그레이션 |

### VERIFY 기준

- [ ] `pytest tests/unit/test_models.py -v` — 전체 통과
- [ ] `pytest tests/unit/test_config.py -v` — 전체 통과
- [ ] `pytest tests/integration/test_database.py -v` — 전체 통과
- [ ] 커버리지: `app/models/` 90%+, `app/core/` 80%+

---

## 3.3 [3] Backend: News Collector

### RED — 테스트 먼저 작성

```python
# tests/unit/test_dedup.py
class TestDedup:
    def test_same_url_is_duplicate(self):
        """동일 URL → 중복 판정"""

    def test_different_url_is_not_duplicate(self):
        """다른 URL → 비중복"""

    def test_same_title_different_source(self):
        """동일 제목 + 다른 출처 → 중복 판정 (유사도 기반)"""

    def test_empty_url_handling(self):
        """URL 없는 뉴스 처리"""

# tests/integration/test_collectors.py
class TestNaverCollector:
    def test_parse_news_list(self, mock_naver_response):
        """네이버 뉴스 HTML 파싱 → NewsEvent 리스트 반환"""

    def test_collect_minimum_10_items(self, mock_naver_response):
        """최소 10건 수집 확인"""

    def test_extract_stock_code_from_url(self):
        """네이버 URL에서 종목코드 추출"""

    def test_retry_on_failure(self, mock_naver_error):
        """수집 실패 시 재시도 (최대 3회)"""

    def test_exponential_backoff(self, mock_naver_error):
        """재시도 간격이 지수적으로 증가"""

class TestDartCollector:
    def test_parse_disclosure_list(self, mock_dart_response):
        """DART 공시 JSON 파싱"""

    def test_set_is_disclosure_true(self, mock_dart_response):
        """DART 수집 뉴스의 is_disclosure=True"""

    def test_invalid_api_key(self):
        """잘못된 API 키 → 적절한 에러"""

class TestRssCollector:
    def test_parse_rss_feed(self, mock_rss_feed):
        """RSS XML 파싱 → NewsEvent 리스트"""

    def test_handle_malformed_xml(self):
        """잘못된 XML → 에러 없이 빈 리스트 반환"""

class TestScheduler:
    def test_scheduler_triggers_collection(self):
        """스케줄러가 수집 함수를 호출하는지 확인"""

    def test_scheduler_interval(self):
        """설정된 주기(5분)에 맞게 트리거"""
```

### GREEN — 구현 대상

| 파일 | 내용 |
|------|------|
| `app/collectors/naver.py` | 네이버 뉴스 크롤러 |
| `app/collectors/dart.py` | DART API 수집 |
| `app/collectors/rss.py` | RSS 피드 파서 |
| `app/processing/dedup.py` | 중복 제거 |
| `app/collectors/scheduler.py` | APScheduler 설정 |

### VERIFY 기준

- [ ] `pytest tests/unit/test_dedup.py -v` — 전체 통과
- [ ] `pytest tests/integration/test_collectors.py -v` — 전체 통과
- [ ] 커버리지: `app/collectors/` 80%+, `app/processing/dedup.py` 90%+

---

## 3.4 [4] Backend: News Processing

### RED — 테스트 먼저 작성

```python
# tests/unit/test_stock_mapper.py
class TestStockMapper:
    def test_exact_name_match(self):
        """'삼성전자' → '005930'"""

    def test_partial_name_match(self):
        """'삼성전자우' → '005935'"""

    def test_english_name(self):
        """'NAVER' → '035420'"""

    def test_unknown_name_returns_none(self):
        """미등록 종목명 → None"""

    def test_kospi200_coverage(self):
        """KOSPI 200 종목 중 90% 이상 매핑 성공"""

    def test_multiple_stocks_in_title(self):
        """'삼성전자와 SK하이닉스 실적' → ['005930', '000660']"""

    def test_ambiguous_stock_name(self):
        """'삼성' → 다중 매칭 (삼성전자, 삼성SDI, 삼성바이오 등) 처리"""
        results = map_stock("삼성")
        # 모호한 이름은 가장 시가총액이 큰 종목 우선 또는 리스트 반환
        assert len(results) >= 1
        assert "005930" in [r.code for r in results]  # 삼성전자 포함

# tests/unit/test_theme_classifier.py
class TestThemeClassifier:
    def test_ai_theme_detection(self):
        """'AI 반도체 수요 증가' → ['AI', '반도체']"""

    def test_battery_theme(self):
        """'2차전지 양극재' → ['2차전지']"""

    def test_no_theme(self):
        """'날씨가 좋습니다' → []"""

    def test_multiple_themes(self):
        """'AI 기반 바이오 신약' → ['AI', '바이오']"""

# tests/unit/test_sentiment.py
class TestSentiment:
    def test_positive_sentiment(self, mock_openai):
        """긍정 뉴스 → SentimentEnum.positive"""

    def test_negative_sentiment(self, mock_openai):
        """부정 뉴스 → SentimentEnum.negative"""

    def test_neutral_sentiment(self, mock_openai):
        """중립 뉴스 → SentimentEnum.neutral"""

    def test_sentiment_score_range(self, mock_openai):
        """감성 점수가 -1.0 ~ 1.0 범위"""

    def test_openai_api_failure_fallback(self, mock_openai_error):
        """OpenAI API 실패 시 neutral 기본값"""
```

### GREEN — 구현 대상

| 파일 | 내용 |
|------|------|
| `app/processing/stock_mapper.py` | 종목명 ↔ 코드 매핑 (KOSPI 200 사전) |
| `app/processing/theme_classifier.py` | 키워드 기반 테마 분류 |
| `app/processing/sentiment.py` | LLM 기반 감성 분석 |

### VERIFY 기준

- [ ] `pytest tests/unit/test_stock_mapper.py -v` — 전체 통과
- [ ] `pytest tests/unit/test_theme_classifier.py -v` — 전체 통과
- [ ] `pytest tests/unit/test_sentiment.py -v` — 전체 통과
- [ ] 커버리지: `app/processing/` 85%+
- [ ] KOSPI 200 종목 매핑 정확도 90%+

---

## 3.5 [5] Backend: Scoring Engine

### RED — 테스트 먼저 작성

```python
# tests/unit/test_scoring.py
class TestRecency:
    def test_within_1h_returns_100(self):
        """1시간 이내 뉴스 → Recency 100"""

    def test_24h_returns_about_50(self):
        """24시간 경과 → Recency ~50"""

    def test_48h_returns_about_25(self):
        """48시간 경과 → Recency ~25"""

    def test_7d_returns_near_zero(self):
        """7일 경과 → Recency ≈ 0"""

    def test_future_timestamp_clamped(self):
        """미래 시각 → 100으로 클램프"""

    def test_timezone_handling(self):
        """KST/UTC 혼용 시 올바른 시간차 계산"""
        # KST 뉴스(+09:00)와 UTC 기준 서버 간 Recency 정확도
        kst_time = datetime(2024, 1, 1, 9, 0, tzinfo=ZoneInfo("Asia/Seoul"))
        utc_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        # 동일 시각이므로 Recency 차이 없어야 함
        assert abs(calc_recency(kst_time) - calc_recency(utc_time)) < 1.0

class TestFrequency:
    def test_zero_news_returns_zero(self):
        """뉴스 0건 → Frequency 0"""

    def test_linear_scaling(self):
        """뉴스 수에 비례하여 점수 증가"""

    def test_max_cap_at_100(self):
        """상한 100 초과 불가"""

    def test_24h_window(self, sample_news_events):
        """24시간 윈도우 내 뉴스만 카운트"""

class TestSentimentScore:
    def test_positive_returns_high(self):
        """positive + score 0.8 → 높은 점수"""

    def test_negative_returns_low(self):
        """negative + score -0.8 → 낮은 점수"""

    def test_neutral_returns_mid(self):
        """neutral → 중간 점수 (50)"""

class TestDisclosureBonus:
    def test_disclosure_gives_100(self):
        """is_disclosure=True → 100"""

    def test_no_disclosure_gives_0(self):
        """is_disclosure=False → 0"""

class TestNewsScore:
    def test_weighted_sum(self):
        """최종 점수 = Recency*0.4 + Frequency*0.3 + Sentiment*0.2 + Disclosure*0.1"""

    def test_score_range_0_to_100(self):
        """최종 점수 0-100 범위"""

    def test_all_max_returns_100(self):
        """모든 요소 100 → 최종 100"""

    def test_all_zero_returns_0(self):
        """모든 요소 0 → 최종 0"""

    def test_disclosure_increases_score(self, sample_news_events):
        """공시 포함 시 점수 상승 확인 (다른 조건 동일)"""

# tests/unit/test_aggregator.py
class TestAggregator:
    def test_aggregate_by_stock(self, sample_news_events):
        """종목별 집계 결과 확인"""

    def test_theme_strength_calculation(self, sample_news_events):
        """테마 강도 점수 계산"""

    def test_top_stocks_per_theme(self, sample_news_events):
        """테마별 상위 종목 리스트"""

    def test_sentiment_avg_calculation(self, sample_news_events):
        """sentiment_avg = 종목별 감성 점수 평균값 (-1.0 ~ 1.0)"""
        result = aggregate_by_stock(sample_news_events)
        for stock in result:
            assert -1.0 <= stock.sentiment_avg <= 1.0
        # 전부 positive인 종목 → sentiment_avg > 0
        # 전부 negative인 종목 → sentiment_avg < 0
```

### GREEN — 구현 대상

| 파일 | 내용 |
|------|------|
| `app/scoring/engine.py` | 점수 계산 (4요소 + 가중합) |
| `app/scoring/aggregator.py` | 종목별/테마별 집계 |

### VERIFY 기준

- [ ] `pytest tests/unit/test_scoring.py -v` — 전체 통과
- [ ] `pytest tests/unit/test_aggregator.py -v` — 전체 통과
- [ ] 커버리지: `app/scoring/` 90%+
- [ ] 시나리오 테스트: 동일 조건 변경 시 점수 변화 일관성

---

## 3.6 [6] Backend: REST API 서버

### RED — 테스트 먼저 작성

```python
# tests/integration/test_api_news.py
class TestNewsScoreEndpoint:
    async def test_get_news_score_success(self, async_client, sample_news_events):
        """GET /news/score?stock=005930 → 200 + NewsScoreResponse"""

    async def test_get_news_score_missing_stock(self, async_client):
        """GET /news/score → 422 (stock 파라미터 누락)"""

    async def test_get_news_score_unknown_stock(self, async_client):
        """GET /news/score?stock=999999 → 200 + score=0"""

class TestNewsTopEndpoint:
    async def test_get_top_news(self, async_client, sample_news_events):
        """GET /news/top?market=KR → 200 + 정렬된 종목 리스트"""

    async def test_top_news_limit(self, async_client, sample_news_events):
        """GET /news/top?market=KR&limit=5 → 최대 5건"""

    async def test_top_news_missing_market(self, async_client):
        """GET /news/top → 422"""

class TestNewsLatestEndpoint:
    async def test_get_latest_news(self, async_client, sample_news_events):
        """GET /news/latest → 200 + 페이지네이션 응답"""

    async def test_latest_pagination(self, async_client, sample_news_events):
        """GET /news/latest?offset=10&limit=5 → 올바른 오프셋"""

    async def test_latest_market_filter(self, async_client, sample_news_events):
        """GET /news/latest?market=KR → KR 뉴스만 반환"""

    async def test_latest_response_has_published_at(self, async_client, sample_news_events):
        """응답 항목에 published_at 필드 존재 (timestamp 아님)"""

# tests/integration/test_api_stocks.py
class TestStockTimelineEndpoint:
    async def test_get_timeline(self, async_client, sample_news_events):
        """GET /stocks/005930/timeline → 200 + 타임라인"""

    async def test_timeline_days_param(self, async_client, sample_news_events):
        """GET /stocks/005930/timeline?days=3 → 3일치"""

    async def test_timeline_unknown_stock(self, async_client):
        """GET /stocks/999999/timeline → 200 + 빈 타임라인"""

# tests/integration/test_api_themes.py
class TestThemeStrengthEndpoint:
    async def test_get_theme_strength(self, async_client, sample_theme_strength):
        """GET /theme/strength → 200 + 테마 리스트"""

    async def test_theme_strength_sorted(self, async_client, sample_theme_strength):
        """strength_score 내림차순 정렬"""

# tests/integration/test_api_health.py
class TestHealthEndpoint:
    async def test_health_check(self, async_client):
        """GET /health → 200 + status='ok'"""

    async def test_health_version(self, async_client):
        """version='1.0.0'"""

# tests/unit/test_schemas.py
class TestSentimentEnum:
    def test_valid_values(self):
        """positive, neutral, negative만 허용"""

    def test_invalid_value_raises(self):
        """'unknown' → ValidationError"""

class TestNewsItemSchema:
    def test_has_market_field(self):
        """NewsItem에 market 필드 존재"""

    def test_has_source_url_field(self):
        """NewsItem에 source_url 필드 존재"""

    def test_has_published_at_field(self):
        """NewsItem에 published_at 필드 존재 (timestamp 아님)"""

class TestErrorResponse:
    def test_global_exception_handler(self, async_client):
        """처리되지 않은 예외 → 500 + 표준 에러 응답"""

class TestCORS:
    async def test_cors_allowed_origin(self, async_client):
        """허용된 origin → Access-Control-Allow-Origin 헤더 포함"""
        response = await async_client.options(
            "/api/news/top",
            headers={"Origin": "http://localhost:5173"}
        )
        assert "access-control-allow-origin" in response.headers

    async def test_cors_disallowed_origin(self, async_client):
        """허용되지 않은 origin → CORS 헤더 미포함"""
        response = await async_client.options(
            "/api/news/top",
            headers={"Origin": "http://evil.com"}
        )
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"

class TestDateSerialization:
    async def test_date_field_iso_format(self, async_client, sample_theme_strength):
        """DB DATE 필드 → API 응답에서 ISO 문자열로 직렬화"""
        resp = await async_client.get("/api/theme/strength")
        data = resp.json()
        for item in data:
            # date 필드가 "2024-01-15" 형식의 문자열
            assert isinstance(item["date"], str)
            datetime.strptime(item["date"], "%Y-%m-%d")  # 파싱 가능해야 함

    async def test_published_at_iso_format(self, async_client, sample_news_events):
        """published_at → ISO 8601 datetime 문자열로 직렬화"""
        resp = await async_client.get("/api/news/latest")
        for item in resp.json()["items"]:
            assert "T" in item["published_at"]  # ISO 8601 형식
```

### GREEN — 구현 대상

| 파일 | 내용 |
|------|------|
| `app/main.py` | FastAPI 앱 + CORS + 에러 핸들러 |
| `app/api/router.py` | 라우터 통합 |
| `app/api/news.py` | /news/* 엔드포인트 |
| `app/api/themes.py` | /theme/* 엔드포인트 |
| `app/api/stocks.py` | /stocks/* 엔드포인트 |
| `app/api/health.py` | /health 엔드포인트 |
| `app/schemas/common.py` | SentimentEnum, TimelinePoint, etc. |
| `app/schemas/news.py` | 뉴스 관련 스키마 |
| `app/schemas/theme.py` | 테마 관련 스키마 |

### VERIFY 기준

- [ ] `pytest tests/integration/test_api_*.py -v` — 전체 통과
- [ ] `pytest tests/unit/test_schemas.py -v` — 전체 통과
- [ ] 커버리지: `app/api/` 85%+, `app/schemas/` 95%+
- [ ] Swagger UI (`/docs`) 정상 렌더링
- [ ] CORS 허용/차단 테스트 통과
- [ ] DATE/datetime 직렬화 테스트 통과 (ISO 형식 확인)

---

## 3.7 [7] Backend: Redis Pub/Sub + WebSocket

### RED — 테스트 먼저 작성

```python
# tests/integration/test_redis_pubsub.py
class TestRedisPubSub:
    async def test_publish_breaking_news(self, fake_redis):
        """속보 이벤트 Redis 발행 확인"""

    async def test_subscribe_receives_event(self, fake_redis):
        """구독자가 이벤트 수신"""

    async def test_breaking_threshold(self, fake_redis):
        """score < 80 → 이벤트 미발행"""

    async def test_above_threshold_publishes(self, fake_redis):
        """score >= 80 → 이벤트 발행"""

    async def test_channel_name_by_market(self, fake_redis):
        """KR → news_breaking_kr, US → news_breaking_us"""

# tests/integration/test_websocket.py
class TestWebSocket:
    async def test_connect(self, async_client):
        """WS /ws/news 연결 성공"""

    async def test_receive_breaking_news(self, async_client, fake_redis):
        """속보 발행 시 WebSocket 메시지 수신"""

    async def test_receive_score_update(self, async_client, fake_redis):
        """스코어 변동 시 WebSocket 메시지 수신"""

    async def test_ping_pong(self, async_client):
        """서버 ping → 클라이언트 pong"""

    async def test_message_format(self, async_client, fake_redis):
        """메시지 type + data 구조 확인"""

    async def test_connection_timeout(self, async_client):
        """클라이언트 무응답 시 서버가 일정 시간 후 연결 종료"""
        # idle 타임아웃 (예: 60초) 후 서버가 연결 해제
        # 테스트에서는 짧은 타임아웃으로 설정하여 검증

    async def test_max_connections_limit(self, async_client):
        """동시 WebSocket 연결 수 제한 (예: 100)"""
        # 최대 연결 수 초과 시 새 연결 거부 또는 가장 오래된 연결 해제
        # 설정된 MAX_WS_CONNECTIONS 값 기반으로 검증
```

### GREEN — 구현 대상

| 파일 | 내용 |
|------|------|
| `app/core/redis.py` | Redis Pub/Sub 발행/구독 |
| `app/api/news.py` (WebSocket) | WS /ws/news 엔드포인트 |

### VERIFY 기준

- [ ] `pytest tests/integration/test_redis_pubsub.py -v` — 전체 통과
- [ ] `pytest tests/integration/test_websocket.py -v` — 전체 통과
- [ ] 커버리지: WebSocket 관련 코드 80%+
- [ ] 타임아웃 및 동시 연결 제한 테스트 통과

---

## 3.8 [8] Frontend: 프로젝트 설정

### RED — 테스트 먼저 작성

```typescript
// tests/api/client.test.ts
describe('API Client', () => {
  test('base URL이 올바르게 설정됨', () => { });
  test('에러 응답 시 적절한 에러 throw', () => { });
  test('타임아웃 설정 확인', () => { });
});

// tests/api/news.test.ts
describe('News API', () => {
  test('fetchTopNews가 올바른 URL 호출', () => { });
  test('fetchLatestNews 페이지네이션 파라미터 전달', () => { });
  test('fetchNewsScore 종목코드 전달', () => { });
});

// tests/api/themes.test.ts
describe('Themes API', () => {
  test('fetchThemeStrength 마켓 파라미터 전달', () => { });
});

// tests/api/stocks.test.ts
describe('Stocks API', () => {
  test('fetchStockTimeline 종목코드 + days 전달', () => { });
});

// tests/components/Loading.test.tsx
describe('Loading', () => {
  test('스피너가 렌더링됨', () => { });
  test('커스텀 메시지 표시', () => { });
});

// tests/components/ErrorBoundary.test.tsx
describe('ErrorBoundary', () => {
  test('자식 에러 발생 시 fallback UI 표시', () => { });
  test('정상 시 자식 컴포넌트 렌더링', () => { });
});
```

### GREEN — 구현 대상

| 파일 | 내용 |
|------|------|
| `src/api/client.ts` | API 클라이언트 인스턴스 |
| `src/api/news.ts` | 뉴스 API 함수 |
| `src/api/themes.ts` | 테마 API 함수 |
| `src/api/stocks.ts` | 종목 API 함수 |
| `src/types/*.ts` | TypeScript 타입 정의 |
| `src/utils/*.ts` | 유틸리티 |
| `src/components/common/Loading.tsx` | 로딩 컴포넌트 |
| `src/components/common/ErrorBoundary.tsx` | 에러 바운더리 |

### VERIFY 기준

- [ ] `npm run test -- --run` — 전체 통과
- [ ] API 클라이언트 및 공통 컴포넌트 커버리지 80%+

---

## 3.9 [9] Frontend: 대시보드 페이지

### RED — 테스트 먼저 작성

```typescript
// tests/pages/DashboardPage.test.tsx
describe('DashboardPage', () => {
  test('Top 종목 카드가 렌더링됨', async () => { });
  test('뉴스 피드 리스트가 렌더링됨', async () => { });
  test('테마 강도 차트가 렌더링됨', async () => { });
  test('KR/US 탭 전환 시 데이터 갱신', async () => { });
  test('로딩 상태 표시', () => { });
  test('에러 상태 표시', () => { });
});

// tests/components/TopStockCards.test.tsx
describe('TopStockCards', () => {
  test('종목명, 스코어, 감성 배지 표시', () => { });
  test('스코어에 따른 색상 구분', () => { });
  test('종목 클릭 시 상세 페이지 이동', () => { });
});

// tests/components/NewsCard.test.tsx
describe('NewsCard', () => {
  test('제목, 종목명, 점수, 출처 표시', () => { });
  test('감성 배지 색상 (positive=green, negative=red)', () => { });
  test('published_at 날짜 포맷팅', () => { });
});

// tests/components/MarketSelector.test.tsx
describe('MarketSelector', () => {
  test('KR/US 탭 렌더링', () => { });
  test('탭 클릭 시 onChange 콜백 호출', () => { });
  test('활성 탭 스타일 적용', () => { });
});

// tests/hooks/useTopNews.test.ts
describe('useTopNews', () => {
  test('마켓별 데이터 fetch', async () => { });
  test('30초 자동 새로고침', async () => { });
  test('에러 시 isError=true', async () => { });
});
```

### 접근성(a11y) 테스트 참고

> 모든 Frontend 컴포넌트 테스트에서 기본적인 접근성 검증을 포함한다:
> - `role`, `aria-label` 등 ARIA 속성이 올바르게 적용되었는지
> - 키보드 네비게이션이 동작하는지 (탭 이동, Enter 클릭)
> - 스크린 리더용 텍스트가 존재하는지

```typescript
// 접근성 기본 패턴 (모든 컴포넌트 테스트에 적용)
test('접근성: 적절한 ARIA 속성', () => {
  render(<Component />);
  // 주요 요소에 role 또는 aria-label 존재
  expect(screen.getByRole('region')).toBeInTheDocument();
});

test('접근성: 키보드 네비게이션', async () => {
  render(<Component />);
  const user = userEvent.setup();
  await user.tab();
  // 첫 번째 인터랙티브 요소에 포커스
  expect(document.activeElement).toHaveAttribute('tabindex');
});
```

### VERIFY 기준

- [ ] `npm run test -- tests/pages/DashboardPage.test.tsx` — 전체 통과
- [ ] `npm run test -- tests/components/` — 대시보드 관련 전체 통과
- [ ] 컴포넌트 커버리지 70%+
- [ ] 주요 컴포넌트 a11y 기본 테스트 포함

---

## 3.10 [10] Frontend: 종목 상세 페이지

### RED — 테스트 먼저 작성

```typescript
// tests/pages/StockDetailPage.test.tsx
describe('StockDetailPage', () => {
  test('URL 파라미터에서 종목코드 추출', () => { });
  test('종목명과 스코어 표시', async () => { });
  test('존재하지 않는 종목 → 에러 메시지', async () => { });
});

// tests/components/ScoreTimeline.test.tsx
describe('ScoreTimeline', () => {
  test('7일 데이터 포인트 렌더링', () => { });
  test('Recharts 라인 차트 렌더링', () => { });
  test('빈 데이터 → "데이터 없음" 메시지', () => { });
});

// tests/components/SentimentPie.test.tsx
describe('SentimentPie', () => {
  test('positive/neutral/negative 비율 렌더링', () => { });
  test('각 섹션 색상 확인 (green/gray/red)', () => { });
});

// tests/hooks/useNewsScore.test.ts
describe('useNewsScore', () => {
  test('종목코드로 스코어 fetch', async () => { });
  test('타임라인 데이터 포함', async () => { });
});
```

### VERIFY 기준

- [ ] `npm run test -- tests/pages/StockDetailPage.test.tsx` — 전체 통과
- [ ] ScoreTimeline, SentimentPie 컴포넌트 커버리지 70%+

---

## 3.11 [11] Frontend: 테마 분석 페이지

### RED — 테스트 먼저 작성

```typescript
// tests/pages/ThemeAnalysisPage.test.tsx
describe('ThemeAnalysisPage', () => {
  test('테마 강도 차트 렌더링', async () => { });
  test('테마 클릭 시 관련 종목 표시', async () => { });
  test('강도 순 정렬', async () => { });
});

// tests/components/ThemeStrengthChart.test.tsx
describe('ThemeStrengthChart', () => {
  test('수평 바 차트 렌더링', () => { });
  test('strength_score 순서 반영', () => { });
  test('바 클릭 이벤트', () => { });
});

// tests/components/SentimentIndicator.test.tsx
describe('SentimentIndicator', () => {
  test('positive → 녹색 배지', () => { });
  test('negative → 빨간 배지', () => { });
  test('neutral → 회색 배지', () => { });
  test('숫자 값 표시', () => { });
});

// tests/hooks/useThemeStrength.test.ts
describe('useThemeStrength', () => {
  test('마켓별 테마 데이터 fetch', async () => { });
});
```

### VERIFY 기준

- [ ] `npm run test -- tests/pages/ThemeAnalysisPage.test.tsx` — 전체 통과
- [ ] ThemeStrengthChart, SentimentIndicator 커버리지 70%+

---

## 3.12 [12] Frontend: 실시간 알림

### RED — 테스트 먼저 작성

```typescript
// tests/hooks/useWebSocket.test.ts
describe('useWebSocket', () => {
  test('WebSocket 연결 성공', () => { });
  test('breaking_news 메시지 수신', () => { });
  test('score_update 메시지 수신', () => { });
  test('연결 끊김 후 자동 재연결', () => { });
  test('ping 수신 시 pong 전송', () => { });
});

// tests/components/Toast.test.tsx
describe('Toast', () => {
  test('속보 뉴스 토스트 표시', () => { });
  test('자동 사라짐 (5초)', () => { });
  test('닫기 버튼 동작', () => { });
});

// tests/components/NotificationBell.test.tsx
describe('NotificationBell', () => {
  test('읽지 않은 알림 수 배지', () => { });
  test('클릭 시 드롭다운 표시', () => { });
  test('알림 히스토리 목록', () => { });
  test('알림 클릭 시 읽음 처리', () => { });
});
```

### VERIFY 기준

- [ ] `npm run test -- tests/hooks/useWebSocket.test.ts` — 전체 통과
- [ ] Toast, NotificationBell 커버리지 70%+

---

# 4. Phase 2 — TDD 계획

## 4.1 LLM 프롬프트 튜닝

### RED

```python
# tests/unit/test_sentiment_accuracy.py
class TestSentimentAccuracy:
    def test_accuracy_above_80_percent(self):
        """100건 테스트 샘플 중 80% 이상 정확"""
        labeled_samples = load_labeled_samples()  # 수동 라벨링 데이터
        correct = 0
        for sample in labeled_samples:
            result = analyze_sentiment(sample.text)
            if result == sample.expected:
                correct += 1
        assert correct / len(labeled_samples) >= 0.80
```

## 4.2 미국 뉴스 연동

### RED

```python
# tests/integration/test_us_collectors.py
class TestFinnhubCollector:
    def test_collect_us_news(self, mock_finnhub_response):
        """Finnhub API에서 뉴스 수집"""

    def test_minimum_10_items_daily(self, mock_finnhub_response):
        """일 10건 이상 수집"""

    def test_market_set_to_us(self, mock_finnhub_response):
        """수집 뉴스의 market='US'"""

class TestNewsApiCollector:
    def test_collect_global_news(self, mock_newsapi_response):
        """NewsAPI에서 뉴스 수집"""

    def test_english_stock_mapping(self):
        """'Apple' → 'AAPL'"""
```

## 4.3 뉴스 요약

### RED

```python
# tests/unit/test_summary.py
class TestNewsSummary:
    def test_summary_length(self, mock_openai):
        """요약 길이 100~300자"""

    def test_summary_contains_key_info(self, mock_openai):
        """요약에 종목명, 핵심 이벤트 포함"""

    def test_quality_manual_check(self):
        """20건 수동 검증 → 핵심 정보 포함율 80%+"""
```

## 4.4 실시간 스케줄러 고도화

### RED

```python
# tests/integration/test_scheduler_performance.py
class TestSchedulerPerformance:
    def test_concurrent_collectors(self):
        """KR + US 수집기가 동시 실행 시 간섭 없이 완료"""
        results = run_concurrent_collection(["naver", "dart", "finnhub"])
        assert all(r.success for r in results)

    def test_scheduler_recovery_after_failure(self):
        """수집기 1개 실패 시 나머지는 정상 실행"""
        with mock_collector_failure("naver"):
            results = run_scheduled_collection()
        assert results["dart"].success is True
        assert results["naver"].success is False

    def test_collection_interval_respected(self):
        """설정된 수집 주기(5분)가 정확히 지켜지는지"""
```

## 4.5 Frontend 고도화 — 차트 드릴다운 + 필터

### RED

```typescript
// tests/components/ChartDrilldown.test.tsx
describe('ChartDrilldown', () => {
  test('차트 포인트 클릭 시 드릴다운 패널 표시', async () => {
    render(<ScoreTimeline data={mockTimeline} />);
    await userEvent.click(screen.getByTestId('chart-point-0'));
    expect(screen.getByTestId('drilldown-panel')).toBeInTheDocument();
  });

  test('드릴다운 패널에 해당 시점 뉴스 리스트 표시', async () => {
    // 클릭한 시점의 관련 뉴스 항목이 표시됨
  });

  test('드릴다운 패널 닫기', async () => { });
});

// tests/components/FilterPanel.test.tsx
describe('FilterPanel', () => {
  test('마켓 필터 (KR/US/ALL)', () => { });
  test('기간 필터 (1일/7일/30일)', () => { });
  test('감성 필터 (positive/neutral/negative)', () => { });
  test('필터 적용 시 onFilter 콜백 호출', () => { });
  test('필터 초기화 버튼', () => { });
});
```

## 4.6 Phase 2 VERIFY 기준

- [ ] 감성 분석 정확도 80%+ (100건 샘플 테스트 통과)
- [ ] 미국 뉴스 수집 일 10건+ (통합 테스트 통과)
- [ ] 뉴스 요약 품질 (수동 검증 20건)
- [ ] 스케줄러 동시 실행 + 장애 복구 테스트 통과
- [ ] 차트 드릴다운 + 필터 컴포넌트 테스트 통과
- [ ] 전체 커버리지 유지: Backend 80%+, Frontend 70%+

---

# 5. Phase 3 — TDD 계획

## 5.1 상관관계 데이터

### RED

```python
# tests/unit/test_correlation.py
class TestCorrelation:
    def test_data_collection_6months(self):
        """6개월 이상 데이터 확인"""

    def test_news_price_alignment(self):
        """뉴스 시각과 주가 데이터 시간 정렬"""

    def test_data_alignment_timestamp(self):
        """뉴스 published_at과 주가 타임스탬프가 동일 timezone(UTC) 기준으로 정렬"""
        news_df, price_df = load_aligned_data("005930")
        # 시간 기준 merge 후 NaN 비율 10% 미만
        merged = pd.merge_asof(news_df, price_df, on="timestamp", tolerance=pd.Timedelta("1h"))
        nan_ratio = merged["price"].isna().mean()
        assert nan_ratio < 0.10
```

## 5.2 예측 모델

### RED

```python
# tests/unit/test_prediction.py
class TestPredictionModel:
    def test_backtest_accuracy_60_percent(self):
        """백테스트 정확도 60%+ (1일 주가 방향 예측)"""
        results = run_backtest(model, test_data)
        assert results.accuracy >= 0.60

    def test_correlation_coefficient(self):
        """예측 점수 ↔ 실제 주가 변동 상관계수 0.3+"""
        corr = calculate_correlation(predictions, actuals)
        assert corr >= 0.3

    def test_prediction_score_range(self):
        """예측 점수 0-100 범위"""
```

## 5.3 예측 API 엔드포인트

### RED

```python
# tests/integration/test_api_prediction.py
class TestPredictionEndpoint:
    async def test_get_prediction(self, async_client):
        """GET /stocks/{code}/prediction → 200 + PredictionResponse"""
        resp = await async_client.get("/api/stocks/005930/prediction")
        assert resp.status_code == 200
        data = resp.json()
        assert "prediction_score" in data
        assert "direction" in data  # "up" | "down" | "neutral"

    async def test_prediction_unknown_stock(self, async_client):
        """존재하지 않는 종목 → 200 + null prediction"""
        resp = await async_client.get("/api/stocks/999999/prediction")
        assert resp.json()["prediction_score"] is None

    async def test_prediction_confidence(self, async_client):
        """응답에 confidence 필드 포함 (0.0 ~ 1.0)"""
        resp = await async_client.get("/api/stocks/005930/prediction")
        conf = resp.json()["confidence"]
        assert 0.0 <= conf <= 1.0

# tests/unit/test_prediction_schema.py
class TestPredictionSchema:
    def test_prediction_response_fields(self):
        """PredictionResponse에 필수 필드 존재"""
        schema = PredictionResponse(
            stock_code="005930",
            prediction_score=72.5,
            direction="up",
            confidence=0.85,
            based_on_days=30
        )
        assert schema.direction in ["up", "down", "neutral"]

    def test_direction_enum(self):
        """direction은 up/down/neutral만 허용"""
        with pytest.raises(ValidationError):
            PredictionResponse(direction="unknown", **valid_fields)
```

## 5.4 예측 뷰 컴포넌트

### RED

```typescript
// tests/components/PredictionChart.test.tsx
describe('PredictionChart', () => {
  test('예측 점수 게이지 렌더링', () => {
    render(<PredictionChart score={72.5} direction="up" />);
    expect(screen.getByTestId('prediction-gauge')).toBeInTheDocument();
  });

  test('direction=up → 상승 아이콘 + 녹색', () => {
    render(<PredictionChart score={72.5} direction="up" />);
    expect(screen.getByTestId('direction-icon')).toHaveClass('text-green');
  });

  test('direction=down → 하락 아이콘 + 빨강', () => { });
  test('score=null → "데이터 부족" 메시지', () => { });
  test('confidence 바 렌더링', () => { });
});

// tests/components/PredictionSignal.test.tsx
describe('PredictionSignal', () => {
  test('강한 매수 신호 (score >= 80)', () => {
    render(<PredictionSignal score={85} />);
    expect(screen.getByText(/강한 매수/)).toBeInTheDocument();
  });

  test('약한 매수 신호 (60 <= score < 80)', () => { });
  test('중립 신호 (40 <= score < 60)', () => { });
  test('매도 신호 (score < 40)', () => { });
});

// tests/hooks/usePrediction.test.ts
describe('usePrediction', () => {
  test('종목코드로 예측 데이터 fetch', async () => {
    const { result } = renderHook(() => usePrediction('005930'));
    await waitFor(() => expect(result.current.data).toBeDefined());
    expect(result.current.data.prediction_score).toBeGreaterThanOrEqual(0);
  });

  test('에러 시 isError=true', async () => { });
  test('로딩 중 isLoading=true', () => { });
});
```

## 5.5 Phase 3 VERIFY 기준

- [ ] 백테스트 정확도 60%+ 테스트 통과
- [ ] 상관계수 0.3+ 테스트 통과
- [ ] 예측 API 엔드포인트 테스트 전체 통과
- [ ] 예측 스키마 검증 테스트 통과
- [ ] PredictionChart, PredictionSignal 컴포넌트 테스트 통과
- [ ] usePrediction hook 테스트 통과
- [ ] 대시보드 예측 뷰 렌더링 테스트 통과

---

# 6. TestAgent 실행 가이드

## 6.1 TestAgent 호출 방법

개발 중 각 Task 시작 시 다음 패턴으로 TestAgent를 호출한다:

```
Task(
  subagent_type="oh-my-claudecode:tdd-guide",
  model="sonnet",
  prompt="""
    [RED 단계] StockNews 프로젝트 Task [N]의 테스트를 작성해주세요.
    - 대상 모듈: {모듈 경로}
    - 참고 설계: docs/StockNews-v1.0.md Section {N}
    - 테스트 파일: {테스트 파일 경로}
    - 테스트 케이스: TestAgent.md Section 3.{N} 참조
  """
)
```

## 6.2 VERIFY 단계 호출

구현 완료 후 검증:

```
Task(
  subagent_type="oh-my-claudecode:tdd-guide",
  model="sonnet",
  prompt="""
    [VERIFY 단계] Task [N] 구현을 검증해주세요.
    - 테스트 실행: pytest tests/ -v --cov=app (또는 npm run test)
    - 커버리지 기준: {목표}%+
    - 모든 테스트 통과 확인
    - 실패 시 구체적 수정 가이드 제공
  """
)
```

## 6.3 전체 회귀 테스트

각 Task 완료 후 전체 테스트 스위트 실행:

```bash
# Backend 전체
cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend 전체
cd frontend && npm run test -- --run --coverage

# E2E (Phase 1 완료 후)
cd frontend && npx playwright test
```

## 6.4 CI 통합 (권장)

```yaml
# .github/workflows/test.yml
name: TDD Test Suite
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e ".[dev]"
        working-directory: backend
      - run: pytest tests/ -v --cov=app --cov-fail-under=80
        working-directory: backend

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
        working-directory: frontend
      - run: npm run test -- --run --coverage
        working-directory: frontend
```

---

# 7. 커버리지 목표 요약

| 범위 | 목표 | 측정 도구 |
|------|------|----------|
| Backend 전체 | 80%+ | pytest-cov |
| Backend: scoring/ | 90%+ | pytest-cov |
| Backend: processing/ | 85%+ | pytest-cov |
| Backend: api/ | 85%+ | pytest-cov |
| Backend: models/ | 90%+ | pytest-cov |
| Backend: schemas/ | 95%+ | pytest-cov |
| Frontend 전체 | 70%+ | v8 (Vitest) |
| Frontend: hooks/ | 80%+ | v8 (Vitest) |
| Frontend: api/ | 80%+ | v8 (Vitest) |
| Frontend: components/ | 70%+ | v8 (Vitest) |
| Frontend: pages/ | 70%+ | v8 (Vitest) |
| E2E | 핵심 3개 시나리오 | Playwright |

---

# 8. TestAgent 체크리스트

각 Task 완료 시 아래 항목을 모두 확인:

- [ ] RED: 실패하는 테스트가 먼저 작성되었는가?
- [ ] GREEN: 테스트를 통과하는 최소 구현이 완료되었는가?
- [ ] REFACTOR: 코드 품질 개선이 이루어졌는가? (테스트 통과 유지)
- [ ] 커버리지: 해당 모듈의 커버리지 목표를 달성했는가?
- [ ] 회귀: 전체 테스트 스위트가 통과하는가?
- [ ] 스키마 일치: Pydantic ↔ TypeScript ↔ DB 3자 일치 유지되는가?
- [ ] 엣지 케이스: null, 빈 값, 잘못된 입력에 대한 테스트가 있는가?
- [ ] 에러 경로: 실패 시나리오 (네트워크 에러, API 에러 등) 테스트가 있는가?
- [ ] 접근성(a11y): 주요 Frontend 컴포넌트에 ARIA 속성 + 키보드 네비게이션 테스트가 있는가?
- [ ] CORS: 허용/차단 origin 테스트가 있는가?
- [ ] 직렬화: DB DATE/datetime 필드의 ISO 문자열 변환 테스트가 있는가?
- [ ] 타임존: KST/UTC 혼용 시나리오 테스트가 있는가?

---

# Changelog

## v1.0 (2026-02-18)

* 초기 TestAgent 설계서 작성
* Phase 1/2/3 전체 TDD 계획 수립
* 테스트 인프라 스택 정의
* Task별 RED-GREEN-REFACTOR-VERIFY 사이클 명세
* 커버리지 목표 및 CI 통합 가이드
