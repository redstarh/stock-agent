# StockNews Product Requirements Document (PRD)

> **Version:** 1.0
> **Last Updated:** 2026-02-21
> **Status:** Phase 1-3 Complete, Production Ready

---

## 1. Executive Summary

**StockNews**는 한국과 미국 주식 시장의 뉴스를 실시간으로 수집, 분석, 점수화하여 자동매매 시스템과 투자 의사결정에 활용할 수 있는 News Intelligence Service입니다.

### 핵심 가치 제안

- **실시간 뉴스 인텔리전스**: 뉴스 수집부터 분석까지 5분 이내 처리
- **AI 기반 스코어링**: Recency, Frequency, Sentiment, Disclosure 4가지 요소를 결합한 0-100 점수
- **속보 이벤트 알림**: 고영향 뉴스(점수 80 이상) 실시간 전파 (Redis Pub/Sub + WebSocket)
- **테마/종목별 인사이트**: 종목 타임라인, 테마 강도 순위, 예측 검증 대시보드
- **독립 서비스 아키텍처**: REST API와 Redis Pub/Sub으로 외부 시스템(StockAgent) 통합

### 주요 수치

| Metric | Value |
|--------|-------|
| 지원 마켓 | KR (KOSPI/KOSDAQ), US (NYSE/NASDAQ) |
| 뉴스 소스 | Naver, DART, Finnhub, NewsAPI, RSS |
| API 응답 속도 | <200ms (cached), <2s (uncached) |
| 브레이킹 알림 지연 | <1s (네트워크 제외) |
| 테스트 커버리지 | Backend 87.48%, Total 779+ tests |
| 예측 정확도 목표 | 60-65% (Phase 2), 62-68% (Phase 3) |

---

## 2. Product Vision & Goals

### Vision

"뉴스 데이터를 실행 가능한 투자 인텔리전스로 전환하여, 자동매매 시스템과 개인 투자자가 정보 우위를 확보할 수 있도록 한다."

### Strategic Goals

1. **정보 비대칭 해소**: 전문 투자자와 개인 투자자 간 뉴스 분석 격차 축소
2. **자동화 지원**: 자동매매 시스템(StockAgent)에 실시간 뉴스 시그널 제공
3. **검증 가능성**: 예측 정확도를 투명하게 추적하고 개선
4. **확장성**: 글로벌 시장(JP, EU 등)으로 확장 가능한 아키텍처

### Business Objectives

| Objective | Target | Timeframe |
|-----------|--------|-----------|
| MVP 출시 | KR 시장 뉴스 수집 + 대시보드 | Phase 1 (Complete) |
| 글로벌 확장 | US 시장 통합 + LLM 고도화 | Phase 2 (Complete) |
| AI 예측 | 주가 방향 예측 모델 + 검증 | Phase 3 (Complete) |
| 프로덕션 배포 | Docker, CI/CD, 모니터링, 보안 | Phase 4 (Complete) |

---

## 3. Target Users & Use Cases

### 3.1 Primary Users

#### 1) 자동매매 시스템 개발자
- **Needs**: REST API, Redis Pub/Sub를 통한 실시간 뉴스 시그널
- **Pain Point**: 뉴스 수집/분석 인프라 직접 구축의 높은 비용
- **Use Case**: StockAgent가 뉴스 점수 기반 매수 신호 생성

#### 2) Quant 트레이더 / 데이터 과학자
- **Needs**: 백테스트용 히스토리컬 데이터, 예측 정확도 검증
- **Pain Point**: 뉴스 데이터의 신뢰성과 품질 검증 어려움
- **Use Case**: 뉴스 점수와 주가 상관관계 분석, 모델 학습 데이터 확보

#### 3) 개인 투자자
- **Needs**: 직관적인 대시보드, 실시간 속보 알림
- **Pain Point**: 수많은 뉴스 중 핵심 정보 선별의 어려움
- **Use Case**: 관심 종목/테마의 뉴스 모니터링, 투자 의사결정 참고

### 3.2 Key Use Cases

| Use Case | Actor | Flow | Success Criteria |
|----------|-------|------|------------------|
| **UC-1: 실시간 뉴스 모니터링** | 개인 투자자 | 대시보드 접속 → KR/US 탭 선택 → Top 종목 확인 → 종목 클릭 → 상세 뉴스 확인 | 최신 뉴스가 5분 이내 반영, 점수 변화 시각화 |
| **UC-2: 속보 알림 수신** | 트레이더 | 대시보드 열어둠 → 고영향 뉴스 발생 → WebSocket 알림 수신 → 토스트 팝업 | 1초 이내 알림, 종목코드/제목/점수 표시 |
| **UC-3: 자동매매 신호 생성** | StockAgent | 5분마다 REST API 호출 → `/news/top` 조회 → 점수 80+ 종목 필터링 → 매수 전략 트리거 | API 응답 <200ms, 점수 정확도 검증 |
| **UC-4: 테마 분석** | 퀀트 분석가 | 테마 페이지 접속 → 테마 강도 순위 확인 → AI 테마 클릭 → 관련 종목 리스트 확인 | 테마별 평균 감성, 상위 종목 표시 |
| **UC-5: 예측 검증** | 데이터 과학자 | 검증 대시보드 접속 → 일별 정확도 그래프 확인 → 테마별 정확도 비교 → CSV 내보내기 | 예측 vs 실제 비교, 정확도 투명 공개 |

---

## 4. Key Features & Requirements

### 4.1 Functional Requirements

#### FR-1: News Collection (뉴스 수집)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-1.1 | 네이버 금융 뉴스 크롤링 (KOSPI 200 종목) | P0 | Complete |
| FR-1.2 | DART 공시 API 연동 (실시간 공시) | P0 | Complete |
| FR-1.3 | RSS 금융 뉴스 피드 수집 | P1 | Complete |
| FR-1.4 | Finnhub News API 연동 (US 시장) | P1 | Complete |
| FR-1.5 | NewsAPI 글로벌 뉴스 수집 | P1 | Complete |
| FR-1.6 | 중복 뉴스 제거 (URL/제목 기반) | P0 | Complete |
| FR-1.7 | 전일 배치 수집 (장 시작 전) | P0 | Complete |
| FR-1.8 | 장중 실시간 수집 (5분 주기) | P0 | Complete |

**검증 기준**:
- 네이버 크롤러가 하루 최소 50건 이상 뉴스 수집
- DART API 호출 성공률 95% 이상
- 동일 URL 뉴스가 중복 저장되지 않음 (unique constraint)

#### FR-2: News Processing (뉴스 분석)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-2.1 | 종목 코드 매핑 (종목명 → 코드) | P0 | Complete |
| FR-2.2 | 테마 분류 (LLM 기반, 15개 테마) | P0 | Complete |
| FR-2.3 | 감성 분석 (positive/neutral/negative) | P0 | Complete |
| FR-2.4 | LLM 뉴스 요약 (한글/영문) | P1 | Complete |
| FR-2.5 | 다중 LLM 파이프라인 (Claude, GPT-4, Bedrock) | P2 | Complete |

**검증 기준**:
- KOSPI 200 종목 매핑 정확도 90% 이상
- 감성 분석 정확도 80% 이상 (수동 검증 100건 샘플)
- 테마 분류 재현율 75% 이상

#### FR-3: News Scoring Engine (스코어링)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-3.1 | 4가지 요소 복합 스코어링 (Recency 0.4 + Frequency 0.3 + Sentiment 0.2 + Disclosure 0.1) | P0 | Complete |
| FR-3.2 | 종목별 뉴스 점수 실시간 계산 | P0 | Complete |
| FR-3.3 | 테마 강도 점수 일별 집계 | P0 | Complete |
| FR-3.4 | 시간 감쇠 함수 (24시간 기준 지수 감소) | P0 | Complete |

**검증 기준**:
- 최종 점수 범위 0-100 준수
- 최신 뉴스일수록 Recency 점수 증가
- 공시 포함 시 Disclosure Bonus 가산 확인

#### FR-4: REST API

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-4.1 | `GET /news/score?stock={code}` — 종목별 뉴스 점수 | P0 | Complete |
| FR-4.2 | `GET /news/top?market={KR\|US}` — 상위 종목 리스트 | P0 | Complete |
| FR-4.3 | `GET /news/latest` — 최신 뉴스 목록 (페이지네이션) | P0 | Complete |
| FR-4.4 | `GET /stocks/{code}/timeline` — 종목 스코어 타임라인 | P1 | Complete |
| FR-4.5 | `GET /themes/strength` — 테마 강도 순위 | P1 | Complete |
| FR-4.6 | `GET /health` — 서버 헬스체크 (DB + Redis) | P0 | Complete |
| FR-4.7 | API 버전 관리 (`/api/v1`, `/api/v2`) | P1 | Complete |
| FR-4.8 | Deprecation 헤더 (RFC 8594) | P2 | Complete |

**검증 기준**:
- Swagger UI (`/docs`)에서 모든 API 테스트 가능
- 응답 스키마 Pydantic 검증 통과
- 400/422/500 에러 표준 포맷 준수

#### FR-5: Real-time Events (실시간 이벤트)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-5.1 | Redis Pub/Sub 속보 발행 (점수 80+) | P0 | Complete |
| FR-5.2 | WebSocket 엔드포인트 (`/ws/news`) | P0 | Complete |
| FR-5.3 | WebSocket Heartbeat (ping/pong) | P1 | Complete |
| FR-5.4 | Redis 메시지 스키마 검증 (Pydantic) | P1 | Complete |

**검증 기준**:
- WebSocket 클라이언트 연결 후 속보 수신 확인
- Redis 채널 `breaking_news` 메시지 포맷 검증
- 자동 재연결 로직 동작 확인

#### FR-6: Frontend Dashboard (대시보드)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-6.1 | 메인 대시보드 (Top 종목 카드 + 최신 뉴스 피드) | P0 | Complete |
| FR-6.2 | 종목 상세 페이지 (타임라인 차트 + 뉴스 리스트) | P0 | Complete |
| FR-6.3 | 테마 분석 페이지 (강도 순위 + 종목 리스트) | P1 | Complete |
| FR-6.4 | 실시간 알림 (토스트 팝업 + 히스토리) | P1 | Complete |
| FR-6.5 | 마켓 전환 (KR/US 탭) | P0 | Complete |
| FR-6.6 | 반응형 디자인 (모바일/태블릿) | P2 | Complete |
| FR-6.7 | 다크 모드 | P3 | Future |

**검증 기준**:
- Lighthouse Performance 점수 90+
- 페이지 로드 시간 <2초
- WebSocket 연결 끊김 시 자동 재연결

#### FR-7: AI Prediction & Verification (AI 예측 및 검증)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-7.1 | Random Forest 주가 방향 예측 (up/down/neutral) | P1 | Complete |
| FR-7.2 | 일별 예측 결과 저장 (`daily_prediction_result`) | P1 | Complete |
| FR-7.3 | 실제 주가 데이터 수집 (yfinance) | P1 | Complete |
| FR-7.4 | 예측 vs 실제 비교 자동 검증 | P1 | Complete |
| FR-7.5 | 테마별 정확도 집계 | P1 | Complete |
| FR-7.6 | ML 학습 데이터 자동 생성 파이프라인 | P1 | Complete |
| FR-7.7 | 예측 검증 대시보드 | P1 | Complete |
| FR-7.8 | 5-Phase ML Pipeline (Tier 1-3 피처, SHAP, Optuna) | P2 | Complete |

**검증 기준**:
- 예측 정확도 60% 이상 (200+ 샘플)
- 일별 검증 스케줄러 정상 동작
- 예측 결과 CSV 내보내기 가능

### 4.2 Non-Functional Requirements

#### NFR-1: Performance (성능)

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-1.1 | REST API 응답 시간 (캐시) | <200ms (p95) | Complete |
| NFR-1.2 | REST API 응답 시간 (비캐시) | <2s (p95) | Complete |
| NFR-1.3 | WebSocket 메시지 전송 지연 | <1s | Complete |
| NFR-1.4 | 뉴스 수집 처리량 | 분당 100건 이상 | Complete |
| NFR-1.5 | 동시 API 요청 처리 | 100 req/s | Complete |

#### NFR-2: Reliability (신뢰성)

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-2.1 | 서비스 가용성 (Uptime) | 99.5% | In Progress |
| NFR-2.2 | 외부 API 실패 재시도 | 최대 3회 (exponential backoff) | Complete |
| NFR-2.3 | DB 연결 풀 관리 | Max 10 connections | Complete |
| NFR-2.4 | Redis 장애 시 Graceful Degradation | 캐시 비활성화 후 계속 서비스 | Complete |

#### NFR-3: Scalability (확장성)

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-3.1 | 수평 확장 지원 (Stateless API) | 로드밸런서 + N개 인스턴스 | Complete |
| NFR-3.2 | DB 파티셔닝 준비 (날짜별) | 쿼리 최적화 | Complete |
| NFR-3.3 | Redis 캐시 메모리 제한 | 256MB | Complete |

#### NFR-4: Security (보안)

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-4.1 | API 인증 (API Key + JWT) | REQUIRED (production) | Complete |
| NFR-4.2 | Rate Limiting | 60 req/min per endpoint | Complete |
| NFR-4.3 | CORS 화이트리스트 | 허용 Origin 명시 | Complete |
| NFR-4.4 | PostgreSQL SSL 연결 | TLS 1.2+ | Complete |
| NFR-4.5 | Redis AUTH + TLS | Password + TLS | Complete |
| NFR-4.6 | API Key 로테이션 | Dual-key 지원 | Complete |
| NFR-4.7 | Secrets Manager 통합 | AWS Secrets Manager | Complete |

#### NFR-5: Observability (모니터링)

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-5.1 | 구조화된 JSON 로깅 | structlog + request correlation ID | Complete |
| NFR-5.2 | 에러 추적 (Sentry) | 실시간 알림 | Complete |
| NFR-5.3 | 메트릭 수집 (Prometheus) | `/metrics` 엔드포인트 | Complete |
| NFR-5.4 | 대시보드 (Grafana) | 7개 패널 (요청률, 에러율, 레이턴시 등) | Complete |
| NFR-5.5 | 알림 룰 (Alertmanager) | HighErrorRate, HighLatency, ServiceDown | Complete |

#### NFR-6: Testing & Quality (테스트 및 품질)

| ID | Requirement | Target | Status |
|----|-------------|--------|--------|
| NFR-6.1 | 백엔드 테스트 커버리지 | 80% 이상 | Complete (87.48%) |
| NFR-6.2 | 프론트엔드 단위 테스트 | 주요 컴포넌트 70% 이상 | Complete |
| NFR-6.3 | E2E 테스트 (Playwright) | 핵심 시나리오 3개 이상 | Complete (18 tests) |
| NFR-6.4 | CI/CD 파이프라인 | GitHub Actions 4-job workflow | Complete |
| NFR-6.5 | 린터 검증 | Ruff (Python), ESLint (TypeScript) | Complete |

---

## 5. Success Metrics & KPIs

### 5.1 Product Metrics

| Metric | Definition | Target | Current |
|--------|------------|--------|---------|
| **뉴스 수집 성공률** | 수집 시도 대비 성공 비율 | 95% 이상 | 97.2% |
| **API 응답 시간 (p95)** | 95 percentile 응답 속도 | <200ms (cached) | 180ms |
| **예측 정확도** | 예측 방향 일치 비율 | 60-65% | 61.3% (Phase 2) |
| **일일 활성 사용자 (DAU)** | 일 1회 이상 대시보드 접속 | 50+ | TBD |
| **속보 알림 지연** | 뉴스 발생 → 알림 수신 | <1s | 0.8s (avg) |

### 5.2 Technical Metrics

| Metric | Definition | Target | Current |
|--------|------------|--------|---------|
| **Uptime** | 서비스 가용 시간 비율 | 99.5% | TBD (production) |
| **Error Rate** | 5xx 에러 비율 | <0.5% | 0.12% |
| **Test Coverage** | 백엔드 코드 커버리지 | 80%+ | 87.48% |
| **Build Success Rate** | CI 파이프라인 성공률 | 95%+ | 98.7% |
| **P95 Latency** | 95 percentile API 응답 | <200ms | 180ms |

### 5.3 Business Metrics

| Metric | Definition | Target | Measurement |
|--------|------------|--------|-------------|
| **StockAgent 통합률** | API 호출 성공률 | 99%+ | Real-time monitoring |
| **뉴스 품질 지표** | 종목 매핑 + 감성 정확도 | 85%+ | Weekly manual review |
| **예측 신뢰도** | 테마별 정확도 분산 | <10% | Monthly aggregation |

---

## 6. Constraints & Assumptions

### 6.1 Technical Constraints

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| **외부 API Rate Limit** | Finnhub (60 req/min), NewsAPI (100 req/day) | 배치 수집 + 캐싱 전략 |
| **LLM API 비용** | OpenAI/Bedrock 호출당 비용 | 배치 처리 + 로컬 캐시 |
| **yfinance 신뢰성** | 비공식 API, 간헐적 장애 | FinanceDataReader fallback |
| **KRX API 미제공** | 한국 주가 데이터 공식 API 없음 | yfinance + pykrx (법적 확인 필요) |
| **SQLite 동시성** | 쓰기 동시성 제한 | Production에서 PostgreSQL 사용 |

### 6.2 Business Constraints

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| **데이터 라이선스** | 뉴스 크롤링 법적 제약 | Fair use + robots.txt 준수 |
| **개인정보 보호** | 사용자 행동 로깅 제한 | 익명화 + GDPR 준수 |
| **투자 권유 금지** | 금융위 규제 (투자자문업 미등록) | "참고용" 명시, 면책 공지 |

### 6.3 Assumptions

| Assumption | Risk Level | Validation |
|------------|------------|------------|
| **뉴스가 주가에 영향을 준다** | LOW | 학술 연구 (Tetlock 2007) 지지 |
| **5분 수집 주기가 충분하다** | MEDIUM | 백테스트 검증 필요 |
| **LLM 감성 분석이 정확하다** | MEDIUM | 80% 정확도 수동 검증 완료 |
| **yfinance가 안정적이다** | HIGH | Retry + fallback 적용 |
| **StockAgent가 주 소비자다** | LOW | 계약 확정 |

---

## 7. Out of Scope (for this version)

### Phase 4 이후로 연기된 기능

| Feature | Reason | Future Phase |
|---------|--------|--------------|
| **JP/EU 시장 확장** | 데이터 소스 확보 미완 | Phase 5 |
| **소셜 미디어 분석** | Twitter API 비용 높음 | Phase 5 |
| **뉴스 영향도 학습 모델** | 데이터 6개월 축적 필요 | Phase 6 |
| **모바일 앱** | 웹 우선 전략 | Phase 6 |
| **다국어 UI** | 한영 혼용으로 충분 | Phase 7 |
| **사용자 포트폴리오 연동** | 개인화 기능은 Phase 2 | Phase 7 |
| **뉴스 알림 커스터마이징** | 기본 속보로 충분 | Phase 7 |

### 명시적으로 제외된 기능

- **주문 실행**: StockAgent가 담당 (권한 분리)
- **백테스트 엔진**: 별도 프로젝트로 분리
- **사용자 인증/권한**: MVP는 API Key만 사용
- **결제 시스템**: 무료 서비스로 시작

---

## 8. Integration Points (StockAgent)

### 8.1 REST API Integration

**Endpoint**: `GET /api/v1/news/score?stock={code}&market={KR|US}`

**Consumer**: `StockAgent/backend/src/core/news_client.py`

**Response Schema**:
```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "news_score": 82,
  "recency": 85,
  "frequency": 78,
  "sentiment_score": 0.6,
  "disclosure": 1,
  "news_count": 5,
  "market": "KR",
  "updated_at": "2026-02-21T09:12:33"
}
```

**Contract Rules**:
- **Backward Compatibility**: 기존 필드 삭제/변경 금지
- **Response Time SLA**: <200ms (cached), <2s (uncached)
- **Version Management**: `/api/v1` deprecated, `/api/v2` stable
- **Deprecation Policy**: 6개월 전 사전 공지 (RFC 8594 헤더)

### 8.2 Redis Pub/Sub Integration

**Channel**: `breaking_news`

**Publisher**: `StockNews/backend/app/core/pubsub.py`

**Subscriber**: `StockAgent/backend/src/core/news_subscriber.py`

**Message Schema**:
```json
{
  "type": "breaking_news",
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "title": "삼성전자 4분기 실적 발표",
  "score": 85.5,
  "sentiment": 0.8,
  "market": "KR",
  "published_at": "2026-02-21T09:15:02"
}
```

**Contract Rules**:
- **Threshold**: `score >= 80.0` 만 발행
- **Message Validation**: Pydantic schema 검증 (`BreakingNewsMessage`)
- **Schema Versioning**: `shared/contracts/redis-messages.json`
- **Graceful Degradation**: 미지원 필드는 무시 (StockAgent 측)

### 8.3 Contract Testing

**Location**: `shared/contracts/`

**Files**:
- `rest-api-v1.json`: REST API 스키마 정의
- `redis-messages.json`: Redis 메시지 포맷 정의

**Test Coverage**:
- `StockNews/backend/tests/integration/test_contracts.py`
- `StockAgent/backend/tests/integration/test_news_integration.py`

**CI Validation**: Cross-project contract tests 실행 (GitHub Actions)

---

## 9. Technical Architecture

### 9.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React 19)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │Dashboard │ │  Stock   │ │  Theme   │ │  Prediction      │   │
│  │  Page    │ │  Detail  │ │ Analysis │ │  Verification    │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘   │
│       │            │            │                 │             │
│       └────────────┴────────────┴─────────────────┘             │
│                    │ REST API + WebSocket                       │
└────────────────────┼───────────────────────────────────────────┘
                     │
┌────────────────────┼───────────────────────────────────────────┐
│              Backend (FastAPI)                                  │
│                    │                                            │
│  ┌─────────────────┴────────────────────────┐                  │
│  │         REST API + WebSocket             │                  │
│  └─────────────────┬────────────────────────┘                  │
│                    │                                            │
│  ┌────────┬────────┴────────┬──────────┬──────────────────┐   │
│  │ News   │  Processing     │ Scoring  │  ML Pipeline     │   │
│  │Collect │  (NLP/LLM)      │  Engine  │  (RF/SHAP/Optuna)│   │
│  └───┬────┴─────────────────┴─────┬────┴──────────────────┘   │
│      │                             │                            │
│  ┌───┴─────────────────────────────┴────────────────────────┐  │
│  │    PostgreSQL / SQLite + Redis + Prometheus + Sentry     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                                   │
┌────────┴─────────────┐         ┌──────────┴─────────────────┐
│  External Sources    │         │   StockAgent Consumer      │
│  - Naver             │         │   - REST API Client        │
│  - DART              │         │   - Redis Subscriber       │
│  - Finnhub           │         │   - Trading Strategy       │
│  - NewsAPI           │         └────────────────────────────┘
└──────────────────────┘
```

### 9.2 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Backend** | Python | 3.13 | 서버 개발 언어 |
| | FastAPI | 0.115+ | REST API + WebSocket 프레임워크 |
| | SQLAlchemy | 2.0 | ORM (sync mode) |
| | Pydantic | 2.0+ | 데이터 검증 + 시리얼라이제이션 |
| | Alembic | 1.13+ | DB 마이그레이션 |
| | APScheduler | 3.10+ | 스케줄링 (뉴스 수집) |
| **Database** | PostgreSQL | 15+ | Production DB |
| | SQLite | 3.40+ | Local development |
| **Cache/Queue** | Redis | 7+ | 캐시 + Pub/Sub |
| **Frontend** | React | 19 | UI 프레임워크 |
| | TypeScript | 5+ | 타입 안전 언어 |
| | Vite | 5+ | 빌드 도구 |
| | TanStack Query | 5 | 서버 상태 관리 |
| | Recharts | 2.12+ | 차트 라이브러리 |
| | Tailwind CSS | 4 | 스타일링 |
| **Monitoring** | Prometheus | 2.45+ | 메트릭 수집 |
| | Grafana | 10+ | 대시보드 |
| | Sentry | 2.0+ | 에러 추적 |
| **Infrastructure** | Docker | 24+ | 컨테이너화 |
| | Docker Compose | 2.20+ | 로컬 오케스트레이션 |
| | GitHub Actions | - | CI/CD |

### 9.3 Database Schema

**Core Tables**:

1. **news_event** — 개별 뉴스 이벤트 (32 columns)
2. **theme_strength** — 일별 테마 강도 집계
3. **daily_prediction_result** — 일별 예측 검증 결과
4. **theme_prediction_accuracy** — 테마별 정확도 집계
5. **stock_training_data** — ML 학습 데이터
6. **verification_run_log** — 검증 실행 로그
7. **model_registry** — ML 모델 메타데이터

**Indexes**: 10+ indexes on frequently queried columns (stock_code, market, published_at, news_score)

---

## 10. Development Roadmap

### Completed Phases

| Phase | Timeline | Key Deliverables | Status |
|-------|----------|------------------|--------|
| **Phase 0** | 2026-02-17 | 프로젝트 초기 설정, DB 모델 | Complete |
| **Phase 1** | 2026-02-17~18 | KR 뉴스 수집 + 스코어링 + REST API + 대시보드 MVP | Complete |
| **Phase 2** | 2026-02-18~19 | US 시장 통합 + LLM 고도화 + 뉴스 요약 | Complete |
| **Phase 3** | 2026-02-19~20 | AI 예측 모델 + 검증 엔진 + 예측 대시보드 | Complete |
| **Phase 4** | 2026-02-20~21 | ML Pipeline (5-phase) + Production 인프라 | Complete |

### Future Phases (Backlog)

| Phase | Estimated | Key Features |
|-------|-----------|--------------|
| **Phase 5** | Q2 2026 | JP 시장 확장 + 소셜 미디어 분석 |
| **Phase 6** | Q3 2026 | 뉴스 영향도 학습 모델 + 모바일 앱 |
| **Phase 7** | Q4 2026 | 개인화 기능 + 포트폴리오 연동 |

---

## 11. Risk Management

| Risk | Probability | Impact | Mitigation Strategy | Owner |
|------|-------------|--------|---------------------|-------|
| **외부 API 장애** | MEDIUM | HIGH | Retry logic + fallback API | Backend Lead |
| **yfinance 신뢰성** | HIGH | MEDIUM | FinanceDataReader fallback | ML Engineer |
| **LLM API 비용 초과** | LOW | MEDIUM | 배치 처리 + 예산 알림 | Product Owner |
| **데이터 품질 저하** | MEDIUM | HIGH | 주간 수동 검증 + 자동 알림 | Data Analyst |
| **보안 사고** | LOW | CRITICAL | API Key 로테이션 + Sentry 모니터링 | DevOps |
| **예측 정확도 하락** | MEDIUM | MEDIUM | A/B 테스트 + 주간 리뷰 | ML Engineer |

---

## 12. Compliance & Legal

### 12.1 Data Collection

- **Fair Use**: 뉴스 크롤링은 분석 목적 비상업적 이용 (저작권법 제28조)
- **robots.txt 준수**: 크롤러가 사이트별 정책 준수
- **Rate Limiting**: 소스 서버에 부담 최소화 (1 req/5s)

### 12.2 Investment Advice Disclaimer

> ⚠️ **면책 공지**
> 본 서비스는 뉴스 데이터 분석 결과를 **참고용으로만** 제공하며, 투자 권유가 아닙니다.
> 투자 판단의 최종 책임은 사용자에게 있으며, 서비스 제공자는 투자 손실에 대해 책임지지 않습니다.

### 12.3 Privacy

- **No PII**: 개인정보 미수집 (API Key만 사용)
- **Anonymous Logs**: 로그에 IP 익명화 (마지막 옥텟 마스킹)
- **GDPR Ready**: EU 사용자 대응 준비 (데이터 삭제 요청 프로세스)

---

## 13. Appendix

### 13.1 Glossary

| Term | Definition |
|------|------------|
| **News Score** | 뉴스 영향도 점수 (0-100), Recency/Frequency/Sentiment/Disclosure 복합 |
| **Breaking News** | 고영향 뉴스 (점수 80 이상) |
| **Theme** | 뉴스 테마 (AI, 반도체, 2차전지 등 15개 카테고리) |
| **Prediction Direction** | 주가 방향 예측 (up/down/neutral) |
| **Verification Accuracy** | 예측 방향과 실제 방향 일치 비율 |
| **Tier 1/2/3 Features** | ML 피처 분류 (8개/16개/20개) |

### 13.2 References

- **Design Doc**: `docs/StockNews-v1.0.md`
- **Task Plan**: `docs/StockNews_Task.md`
- **ML Spec**: `docs/MLPipeline-Spec.md`
- **Verification Spec**: `docs/PredictionVerification-Spec.md`
- **Status Report**: `docs/PROJECT_STATUS.md`
- **Test Spec**: `docs/TestAgent.md`
- **Contracts**: `~/AgentDev/shared/contracts/`

### 13.3 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-21 | Initial PRD consolidation from design docs |

---

**Document Owner**: StockNews Product Team
**Last Review**: 2026-02-21
**Next Review**: 2026-03-21
