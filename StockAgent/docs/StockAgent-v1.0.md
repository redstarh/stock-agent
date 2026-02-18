# StockAgent v1.0

## (키움 REST API 기반 한국 주식 자동매매 시스템)

---

# 1. 시스템 목적

Mac 환경에서 Windows/VM 없이
키움증권 REST API(OpenAPI REST/HTTP Gateway)를 활용한

* 코스피/코스닥 자동매매
* 장초 거래대금 대장주 전략
* 뉴스 기반 필터 매매
* 학습 데이터 축적
* **웹 기반 모니터링/관리 대시보드**

※ StockNews 시스템과 완전 분리된 독립 서비스
※ REST 기반 비동기 구조 (이벤트 COM 사용 안함)
※ **Frontend / Backend 독립 개발 구조**

---

# 2. 핵심 설계 원칙

## 2.1 Windows/VM 미사용

기존 방식 (비추천):

* 키움 OpenAPI+ (COM)
* PyQt 이벤트 루프
* Windows 필수

본 설계 (목표):

> REST API + 비동기 Python 구조 (Mac Native)

장점:

* Mac 네이티브 운영 가능
* ClaudeCode 자동 코드 생성 최적
* 마이크로서비스 구조 호환
* 테스트/디버깅 쉬움

## 2.2 Frontend/Backend 분리 원칙

* Backend는 Frontend 없이 **독립 실행 가능** (CLI/자동매매)
* Frontend는 Backend REST API에만 의존
* **API Contract(OpenAPI 스펙) 우선 정의** 후 병렬 개발
* Frontend는 Mock API로 Backend 완성 전 독립 개발 가능

---

# 3. 전체 아키텍처 구조

## 3.1 시스템 전체 구조

```
┌─────────────────────────────────────────────────────┐
│  Frontend (React/Next.js + TypeScript)              │
│  대시보드 / 포트폴리오 / 매매 내역 / 전략 설정       │
│  WebSocket으로 실시간 상태 수신                      │
└──────────────────────┬──────────────────────────────┘
                       │ REST API + WebSocket
┌──────────────────────▼──────────────────────────────┐
│  Backend (FastAPI + asyncio)                         │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐          │
│  │ API Layer│ │ Trade Core│ │ Scheduler │          │
│  │ (FastAPI)│ │ (asyncio) │ │(APSched)  │          │
│  └────┬─────┘ └─────┬─────┘ └─────┬─────┘          │
│       └──────────────┼─────────────┘                 │
│  ┌───────────────────▼──────────────────────┐       │
│  │ kiwoom_client │ news_client │ risk │ strategy │  │
│  └──────────────────────────────────────────┘       │
└──────────────────────┬──────────────────────────────┘
              ┌────────┼────────┐
              ▼        ▼        ▼
          PostgreSQL  Redis   Kiwoom REST API
```

## 3.2 Backend 내부 파이프라인

```
[Kiwoom REST API Server]
      ↓ (HTTPS/REST)
[Market Data Collector]
      ↓
[Opening Scanner Engine]
      ↓
[News Interface Client (StockNews)] ← Redis Subscribe
      ↓
[Strategy Engine]
      ↓
[Risk Management Engine]
      ↓
[Order Execution Client (REST)]
      ↓
[Trade DB + Learning DB]
      ↓
[FastAPI] → REST/WebSocket → [Frontend]
```

---

# 4. 기술 스택

## 4.1 Backend

| 구분 | 기술 | 용도 |
|------|------|------|
| Runtime | Python 3.11 | 메인 런타임 |
| Async | asyncio + httpx | REST 비동기 통신 |
| Web Framework | FastAPI | REST API + WebSocket 서버 |
| ORM | SQLAlchemy 2.0 | DB 모델링 |
| DB | PostgreSQL | 거래/학습 데이터 |
| Cache/PubSub | Redis | 뉴스 이벤트, 캐싱 |
| Data | pandas / numpy | 시세 데이터 처리 |
| Scheduler | APScheduler | 장 시작/종료 스케줄링 |
| Validation | Pydantic v2 | 요청/응답 스키마 |

## 4.2 Frontend

| 구분 | 기술 | 용도 |
|------|------|------|
| Framework | React 18 / Next.js | SPA/SSR |
| Language | TypeScript (strict) | 타입 안전성 |
| Styling | TailwindCSS | UI 스타일링 |
| State | TanStack Query | 서버 상태 관리 |
| Charts | Recharts / Lightweight Charts | 차트/시세 시각화 |
| WebSocket | native WebSocket | 실시간 데이터 수신 |
| Mock | MSW (Mock Service Worker) | Backend 독립 개발용 |

## 4.3 인프라

| 구분 | 기술 | 용도 |
|------|------|------|
| Container | Docker + Docker Compose | 로컬 개발 환경 (PG, Redis) |
| CI | GitHub Actions | 자동 테스트 |
| API Docs | OpenAPI 3.0 (자동 생성) | Frontend/Backend 계약 |

---

# 5. 프로젝트 디렉토리 구조

```
StockAgent/
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   ├── main.py                  # FastAPI 앱 엔트리포인트
│   │   ├── config.py                # 환경 설정 (pydantic-settings)
│   │   ├── database.py              # DB 연결, 세션 관리
│   │   │
│   │   ├── kiwoom_client/           # 키움 REST API 클라이언트
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # 인증 토큰 관리
│   │   │   ├── market.py            # 시세 조회
│   │   │   ├── order.py             # 주문
│   │   │   └── account.py           # 계좌 정보
│   │   │
│   │   ├── core/                    # 매매 핵심 엔진
│   │   │   ├── __init__.py
│   │   │   ├── market_data.py       # 시세 수집 + VWAP + 분봉
│   │   │   ├── scanner.py           # 장초 스캐너 엔진
│   │   │   ├── news_client.py       # StockNews REST + Redis
│   │   │   ├── strategy.py          # 전략 엔진
│   │   │   ├── risk.py              # 리스크 관리
│   │   │   ├── order_executor.py    # 주문 실행 (재시도/슬리피지)
│   │   │   ├── trader.py            # 메인 자동매매 루프
│   │   │   └── learning.py          # 학습 데이터 분석
│   │   │
│   │   ├── api/                     # FastAPI 라우터
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # 메인 라우터 등록
│   │   │   ├── account.py           # 계좌 엔드포인트
│   │   │   ├── trades.py            # 매매 내역 엔드포인트
│   │   │   ├── strategy.py          # 전략 설정 엔드포인트
│   │   │   ├── risk.py              # 리스크 설정 엔드포인트
│   │   │   ├── scanner.py           # 스캐너 엔드포인트
│   │   │   ├── reports.py           # 리포트/통계 엔드포인트
│   │   │   ├── system.py            # 시스템 제어 (start/stop)
│   │   │   └── ws.py                # WebSocket 실시간 push
│   │   │
│   │   └── models/                  # SQLAlchemy + Pydantic
│   │       ├── __init__.py
│   │       ├── db_models.py         # SQLAlchemy ORM 모델
│   │       └── schemas.py           # Pydantic 요청/응답 스키마
│   │
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       └── integration/
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/                     # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx             # 대시보드 (메인)
│   │   │   ├── trades/page.tsx      # 매매 내역
│   │   │   ├── strategy/page.tsx    # 전략 설정
│   │   │   ├── scanner/page.tsx     # 장초 스캐너
│   │   │   └── reports/page.tsx     # 리포트/분석
│   │   │
│   │   ├── components/              # 공통 컴포넌트
│   │   │   ├── Dashboard/
│   │   │   ├── Portfolio/
│   │   │   ├── TradeTable/
│   │   │   └── Charts/
│   │   │
│   │   ├── hooks/                   # Custom hooks
│   │   │   ├── useAccount.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useTrades.ts
│   │   │
│   │   ├── lib/                     # API 클라이언트, 유틸
│   │   │   ├── api.ts               # axios/fetch wrapper
│   │   │   └── types.ts             # 공유 타입 정의
│   │   │
│   │   └── mocks/                   # MSW Mock 핸들러
│   │       ├── handlers.ts
│   │       └── server.ts
│   │
│   └── tests/
│
├── docs/
│   └── StockAgent.md                # 이 문서
│
├── docker-compose.yml               # PostgreSQL + Redis
└── CLAUDE.md
```

---

# 6. Backend 모듈 상세 설계

## 6.1 키움 REST API 클라이언트 (kiwoom_client/)

### auth.py - 인증 토큰 관리

* OAuth 토큰 발급/갱신
* 토큰 만료 자동 감지 + 재발급
* httpx.AsyncClient 기반

### market.py - 시세 조회

* 현재가 조회
* 호가 조회
* 거래량/거래대금 조회

```python
async def get_price(code: str) -> dict:
    url = f"/api/v1/market/price/{code}"
    return await client.get(url)
```

### order.py - 주문

* 매수/매도 주문 생성
* 체결 상태 조회
* 주문 취소

```python
await kiwoom.order_buy(code="005930", qty=10, price=market_price)
```

### account.py - 계좌 정보

* 예수금 조회
* 보유 종목 리스트
* 평가 손익

## 6.2 Market Data Collector (core/market_data.py)

기능:

* 실시간 시세 수집 (REST Polling 또는 WebSocket)
* 거래대금 계산
* 체결강도 추정
* VWAP 계산
* 1분봉 Aggregator

## 6.3 Opening Scanner Engine (core/scanner.py)

장초 전략 조건 (09:00~10:00):

* 거래대금 TOP N
* 거래량 급증 (전일 대비)
* 상승률 상위
* 뉴스 점수 필터

## 6.4 News Interface Client (core/news_client.py)

연동 방식:

* REST 조회 (안정)
* Redis Subscribe (속보 이벤트, 채널: news_breaking_kr)

```python
if news_score > 70 and volume_rank <= 5:
    buy_signal = True
```

## 6.5 Strategy Engine (core/strategy.py)

매수 조건:

* 장초 거래대금 상위
* 뉴스 점수 통과
* 장초 고가 돌파
* VWAP 상단 유지

## 6.6 Order Execution Engine (core/order_executor.py)

기능:

* 주문 생성 (REST)
* 체결 상태 조회
* 분할 매수/매도

## 6.7 Risk Management (core/risk.py)

정책:

* 종목당 비중 ≤ 10%
* 손절: -3% ~ -5%
* 1일 최대 손실 제한
* 동시 보유 종목 제한

---

# 7. Frontend 모듈 상세 설계

## 7.1 대시보드 (메인 페이지)

* 계좌 요약: 예수금, 총 평가액, 일일 손익
* 시스템 상태: 자동매매 running/stopped, 마지막 체결 시간
* 보유 포지션 카드: 종목별 평가손익, 수익률
* 실시간 업데이트 (WebSocket)

## 7.2 매매 내역 페이지

* 매매 기록 테이블 (날짜, 종목, 매수/매도, 수량, 가격, 손익)
* 필터: 날짜 범위, 종목, 전략 태그
* 정렬: 날짜, 손익, 수익률
* 페이지네이션

## 7.3 전략 설정 페이지

* 전략 파라미터 편집 (폼 UI)
  - 거래대금 TOP N 값
  - 뉴스 점수 임계치
  - VWAP 기준값
* 전략 활성화/비활성화 토글
* 파라미터 변경 히스토리

## 7.4 장초 스캐너 뷰

* 실시간 거래대금 TOP N 종목 테이블
* 거래량 급증 표시
* 뉴스 점수 표시
* WebSocket 기반 자동 갱신

## 7.5 리스크 설정 페이지

* 손절률 설정 (-3% ~ -5%)
* 종목당 최대 비중 (%)
* 1일 최대 손실 한도
* 동시 보유 종목 수 제한
* 비상 전체 청산 버튼

## 7.6 리포트/분석 페이지

* 일별 수익률 라인 차트
* 누적 수익 곡선
* 승률 / 평균 수익 통계
* Max Drawdown 시각화
* Best/Worst 패턴 분석

---

# 8. API Contract (Frontend ↔ Backend)

## 8.1 외부 연동 API

### 필수 API

* 키움 REST API (시세 + 주문)
* StockNews REST API (내부 서비스)
* Redis (뉴스 이벤트 수신)

### 무료 데이터 (StockNews 제공)

* DART 공시 API
* 국내 뉴스 크롤링

## 8.2 REST API 엔드포인트

### 시스템

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/health | 시스템 상태 (trading engine running 여부) |
| POST | /api/v1/system/start | 자동매매 시작 |
| POST | /api/v1/system/stop | 자동매매 정지 |

### 계좌

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/account/balance | 예수금, 총 평가액, 일일 손익 |
| GET | /api/v1/account/positions | 보유 포지션 리스트 |

### 매매

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/trades | 매매 내역 (pagination, filter) |
| GET | /api/v1/trades/{id} | 매매 상세 |

### 전략

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/strategy/config | 전략 설정 조회 |
| PUT | /api/v1/strategy/config | 전략 설정 변경 |
| POST | /api/v1/strategy/toggle | 전략 활성화/비활성화 |

### 리스크

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/risk/config | 리스크 설정 조회 |
| PUT | /api/v1/risk/config | 리스크 설정 변경 |
| POST | /api/v1/risk/emergency-sell | 비상 전체 청산 |

### 스캐너

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/scanner/top | 장초 거래대금 TOP N |

### 리포트

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/reports/daily | 일간 리포트 |
| GET | /api/v1/reports/metrics | 학습 메트릭 |

## 8.3 WebSocket

| Path | 설명 |
|------|------|
| WS /ws/live | 실시간 시세, 포지션 변동, 매매 신호, 체결 알림 |

WebSocket 메시지 타입:

```json
{ "type": "price_update", "data": { "code": "005930", "price": 71000, "volume": 12345 } }
{ "type": "position_update", "data": { "code": "005930", "qty": 10, "pnl": 5000 } }
{ "type": "trade_signal", "data": { "code": "005930", "action": "buy", "reason": "volume_leader" } }
{ "type": "order_filled", "data": { "order_id": "...", "code": "005930", "price": 71000 } }
{ "type": "system_status", "data": { "status": "running", "active_positions": 3 } }
```

---

# 9. 데이터베이스 설계

## 9.1 trade_log

| 컬럼 | 타입 | 설명 |
|------|------|------|
| trade_id | UUID (PK) | 거래 고유 ID |
| date | DATE | 거래일 |
| market | VARCHAR(4) | 시장 (KR) |
| stock_code | VARCHAR(10) | 종목 코드 |
| stock_name | VARCHAR(50) | 종목명 |
| side | VARCHAR(4) | buy / sell |
| entry_time | TIMESTAMP | 진입 시간 |
| exit_time | TIMESTAMP | 청산 시간 |
| entry_price | DECIMAL | 진입 가격 |
| exit_price | DECIMAL | 청산 가격 |
| quantity | INTEGER | 수량 |
| pnl | DECIMAL | 실현 손익 |
| pnl_pct | DECIMAL | 수익률 (%) |
| news_score | INTEGER | 매매 시점 뉴스 점수 |
| volume_rank | INTEGER | 매매 시점 거래대금 순위 |
| strategy_tag | VARCHAR(50) | 전략 태그 |
| created_at | TIMESTAMP | 레코드 생성 |

## 9.2 learning_metrics

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL (PK) | 자동 증가 ID |
| date | DATE (UNIQUE) | 집계일 |
| total_trades | INTEGER | 총 거래 수 |
| win_count | INTEGER | 승리 수 |
| win_rate | DECIMAL | 승률 (%) |
| avg_return | DECIMAL | 평균 수익률 (%) |
| max_drawdown | DECIMAL | 최대 낙폭 (%) |
| total_pnl | DECIMAL | 당일 총 손익 |
| best_pattern | VARCHAR(100) | 최고 수익 패턴 |
| worst_pattern | VARCHAR(100) | 최대 손실 패턴 |
| created_at | TIMESTAMP | 레코드 생성 |

## 9.3 positions (실시간 보유)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | SERIAL (PK) | 자동 증가 ID |
| stock_code | VARCHAR(10) | 종목 코드 |
| stock_name | VARCHAR(50) | 종목명 |
| quantity | INTEGER | 보유 수량 |
| avg_price | DECIMAL | 평균 매수가 |
| current_price | DECIMAL | 현재가 |
| unrealized_pnl | DECIMAL | 미실현 손익 |
| stop_loss_price | DECIMAL | 손절 가격 |
| entry_time | TIMESTAMP | 최초 진입 시간 |
| updated_at | TIMESTAMP | 갱신 시간 |

## 9.4 orders (주문 이력)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| order_id | UUID (PK) | 주문 고유 ID |
| stock_code | VARCHAR(10) | 종목 코드 |
| side | VARCHAR(4) | buy / sell |
| order_type | VARCHAR(10) | market / limit |
| quantity | INTEGER | 주문 수량 |
| price | DECIMAL | 주문 가격 |
| filled_quantity | INTEGER | 체결 수량 |
| filled_price | DECIMAL | 체결 가격 |
| status | VARCHAR(20) | pending / filled / cancelled / failed |
| kiwoom_order_id | VARCHAR(50) | 키움 주문번호 |
| created_at | TIMESTAMP | 주문 생성 |
| updated_at | TIMESTAMP | 상태 갱신 |

---

# 10. 개발 태스크 총괄 (Phase별)

## Phase 1: MVP (기반 인프라 + 핵심 루프)

### Backend

| ID | 태스크 | 모듈 | 선행 | 설명 |
|----|--------|------|------|------|
| B-1 | 프로젝트 초기 셋업 | infra | - | pyproject.toml, 디렉토리, pytest, Docker Compose |
| B-2 | DB 스키마 + ORM 모델 | models | B-1 | trade_log, learning_metrics, positions, orders |
| B-3 | 키움 인증 클라이언트 | kiwoom/auth | B-1 | 토큰 발급/갱신/캐싱 |
| B-4 | 키움 시세 클라이언트 | kiwoom/market | B-3 | 현재가, 호가, 거래량 조회 |
| B-5 | 키움 주문 클라이언트 | kiwoom/order | B-3 | 매수/매도, 체결조회 |
| B-6 | 키움 계좌 클라이언트 | kiwoom/account | B-3 | 잔고, 보유종목, 예수금 |
| B-7 | Market Data Collector | core/market_data | B-4 | 시세수집, 거래대금, VWAP, 분봉 |
| B-8 | 기본 자동매매 루프 | core/trader | B-5,B-7 | asyncio 메인루프 |
| B-9 | FastAPI 기본 API | api | B-2 | health, account, positions 엔드포인트 |

### Frontend

| ID | 태스크 | 선행(Backend) | 설명 |
|----|--------|--------------|------|
| F-1 | 프로젝트 초기 셋업 | - | Next.js + TS + Tailwind |
| F-2 | API 클라이언트 + Mock | - | fetch wrapper + MSW |
| F-3 | 인증 UI | B-9 (mock 가능) | API 키 설정 |
| F-4 | 계좌 대시보드 | B-9 (mock 가능) | 예수금, 평가액, 손익 |
| F-5 | 포지션 현황 | B-9 (mock 가능) | 보유종목 리스트 |
| F-6 | 실시간 상태 | B-18 (mock 가능) | WebSocket 시스템 상태 |

## Phase 2: 전략 연동

### Backend

| ID | 태스크 | 모듈 | 선행 | 설명 |
|----|--------|------|------|------|
| B-10 | Opening Scanner | core/scanner | B-7 | 거래대금 랭킹, 대장주, Range |
| B-11 | StockNews REST 연동 | core/news_client | B-1 | /news/score, 캐싱 |
| B-12 | Redis 뉴스 구독 | core/news_client | B-11 | news_breaking_kr 채널 |
| B-13 | Strategy Engine | core/strategy | B-10,B-11 | Rule 기반, YAML 설정 |
| B-14 | Risk Management | core/risk | B-2 | 손절, 사이징, 일일한도, 청산 |
| B-15 | Order Execution 고도화 | core/order_executor | B-5,B-14 | 분할매매, 재주문, 슬리피지 |
| B-16 | 매매 내역 API | api/trades | B-2,B-9 | 매매기록 CRUD + 필터 |
| B-17 | 전략 관리 API | api/strategy | B-13 | 설정 조회/수정, on/off |
| B-18 | WebSocket 실시간 | api/ws | B-8 | 시세, 포지션, 신호 push |

### Frontend

| ID | 태스크 | 선행(Backend) | 설명 |
|----|--------|--------------|------|
| F-7 | 매매 내역 페이지 | B-16 (mock 가능) | 테이블, 필터, 페이지네이션 |
| F-8 | 전략 설정 페이지 | B-17 (mock 가능) | 파라미터 편집, 토글 |
| F-9 | 장초 스캐너 뷰 | B-10,B-18 (mock 가능) | 실시간 TOP N |
| F-10 | 리스크 설정 UI | B-14 (mock 가능) | 손절/비중/한도 설정 |
| F-11 | 주문 모니터링 | B-18 (mock 가능) | 실시간 주문, 체결알림 |

## Phase 3: 고도화

### Backend

| ID | 태스크 | 모듈 | 선행 | 설명 |
|----|--------|------|------|------|
| B-19 | Learning DB | core/learning | B-2 | 패턴분석, 승률/수익률 집계 |
| B-20 | 자동 리포트 | core/report | B-19 | 일간/주간 리포트 생성 |
| B-21 | 파라미터 튜닝 | core/tuner | B-19,B-13 | 자동 최적화 |
| B-22 | 리포트/통계 API | api/reports | B-19,B-20 | 리포트, 메트릭 엔드포인트 |

### Frontend

| ID | 태스크 | 선행(Backend) | 설명 |
|----|--------|--------------|------|
| F-12 | 성과 분석 차트 | B-22 (mock 가능) | 수익률, 누적수익 (Recharts) |
| F-13 | 학습 메트릭 | B-22 (mock 가능) | drawdown, 패턴 시각화 |
| F-14 | 리포트 뷰어 | B-22 (mock 가능) | 일간/주간 리포트 조회 |

---

# 11. 개발 일정 (권장)

```
Week 1-2:  B-1 ~ B-6   (인프라 + 키움 클라이언트)
           F-1 ~ F-2   (프론트 셋업 + Mock)

Week 3-4:  B-7 ~ B-9   (시세 수집 + 매매 루프 + 기본 API)
           F-3 ~ F-5   (인증 + 대시보드 + 포지션)

Week 5-6:  B-10 ~ B-15 (스캐너 + 뉴스 + 전략 + 리스크)
           F-6 ~ F-8   (실시간 + 매매내역 + 전략설정)

Week 7-8:  B-16 ~ B-18 (API 확장 + WebSocket)
           F-9 ~ F-11  (스캐너뷰 + 리스크 + 주문모니터)

Week 9+:   B-19 ~ B-22 (학습 + 리포트)
           F-12 ~ F-14 (차트 + 분석)
```

---

# 12. 실행 프로세스

```
process 1: stocknews_service (FastAPI) — 별도 레포
process 2: stockagent backend (FastAPI + asyncio trader)
process 3: stockagent frontend (Next.js dev server)
process 4: redis
process 5: postgres
```

개발 환경 실행:

```bash
# 인프라 (PostgreSQL + Redis)
docker-compose up -d

# Backend
cd backend && uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev -- --port 3000
```

※ Windows / VM / COM / PyQt 전혀 불필요

---

# 13. 미국 시장 확장 계획 (Phase 2)

* StockAgent-US 별도 서비스
* IBKR / Alpaca REST API 사용
* StockNews 공통 재사용
* Strategy Core / Frontend 재사용 가능

---

# 14. Mac 운영 안정성 고려사항

* 절전 모드 OFF 필수
* asyncio 기반 비동기 구조 권장
* API Rate Limit 관리 필수 (키움 초당 5회 제한 등)
* 로그 롤링 (일 단위)
* 네트워크 장애 대비 재시도 로직 (exponential backoff)
* PostgreSQL 커넥션 풀 관리

---

# 15. 보완 필요 사항

1. **키움 REST API 실제 스펙 확인** - "OpenAPI REST/HTTP Gateway 가정" → 실제 엔드포인트/인증 방식 확정 필요
2. **배포 환경 결정** - Docker Compose 로컬 vs 클라우드 (추후 결정)
3. **에러 핸들링 정책 구체화** - Rate Limit, 네트워크 장애, 키움 API 에러 코드별 처리
4. **보안** - API 키 관리 방법, 환경변수 전략
5. **모니터링/알림** - 시스템 이상 시 알림 채널 (Slack, Telegram 등)

---

# 16. 최종 설계 요약

핵심 구조:

* **키움 REST API 기반** (COM 제거) — Mac Native 자동매매
* **Frontend/Backend 완전 분리** — API Contract 기반 병렬 개발
* **Backend**: FastAPI + asyncio + PostgreSQL + Redis
* **Frontend**: React/Next.js + TypeScript + TailwindCSS + WebSocket
* **StockNews 완전 분리 연동** — REST + Redis pub/sub
* **비동기 Python 아키텍처** — httpx + asyncio 기반 REST 파이프라인

개발 범위:

* Backend 태스크: B-1 ~ B-22 (22개)
* Frontend 태스크: F-1 ~ F-14 (14개)
* 총 36개 태스크, 3 Phase 구성

핵심 전략:

* 장초 거래대금 대장주 전략 (09:00~10:00)
* 뉴스 점수 필터 (StockNews 연동)
* VWAP 기반 진입, 자동 손절/리스크 관리
