# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StockAgent - Kiwoom REST API 기반 한국 주식 자동매매 시스템. Mac 환경에서 Windows/VM 없이 키움증권 REST API를 활용한 비동기 자동매매 플랫폼.

**Status**: 전체 구현 완료 (Sprint 0~6, 36개 태스크 완료) | 테스트 커버리지 최적화 완료

Separate from the StockNews system - communicates via REST API and Redis pub/sub.

## Tech Stack

### Backend
- **Python 3.13** (venv: `backend/.venv`)
- **FastAPI** for REST API + WebSocket
- **httpx** for async REST communication
- **SQLAlchemy 2.0** (async) for ORM
- **PostgreSQL** (via asyncpg) + **Redis** (via redis-py)
- **Pydantic v2** + **pydantic-settings** for config/validation
- **APScheduler** for market-hours scheduling
- **pandas / numpy** for data processing

### Frontend
- **Next.js 16** + **React 19** + **TypeScript**
- **TailwindCSS v4** for styling
- **TanStack Query** for server state
- **Recharts** for charts
- **MSW v2** for API mocking
- **Jest 30** + **React Testing Library** for tests

## Commands

### Backend
```bash
# Activate venv
source backend/.venv/bin/activate

# Run all tests
cd backend && .venv/bin/pytest -v

# Run tests with coverage
cd backend && .venv/bin/pytest --cov=src --cov-report=term-missing -v

# Run specific module tests
cd backend && .venv/bin/pytest tests/unit/kiwoom_client/test_auth.py -v

# Start dev server (after B-9 complete)
cd backend && uvicorn src.main:app --reload --port 8000
```

### Frontend
```bash
# Run all tests
cd frontend && npx jest --no-cache

# Run specific test
cd frontend && npx jest tests/setup.test.tsx

# Run with coverage
cd frontend && npx jest --coverage

# Start dev server
cd frontend && npm run dev
```

### Infrastructure
```bash
# Start PostgreSQL + Redis
docker-compose up -d
```

## Architecture

REST-based async pipeline (no COM/PyQt/Windows dependencies):

```
Kiwoom REST API → Market Data Collector → Opening Scanner Engine
                                              ↓
                  StockNews REST/Redis → Strategy Engine → Risk Management → Order Execution → Trade DB
                                                                                                  ↓
                  Frontend (Next.js) ← REST API + WebSocket ← FastAPI ← Trade DB
```

## Project Structure

```
StockAgent/
├── backend/
│   ├── pyproject.toml          # Python dependencies
│   ├── .env                    # Environment config (gitignored)
│   ├── .env.example
│   ├── src/
│   │   ├── __init__.py         # Logging setup (auto-init)
│   │   ├── config.py           # pydantic-settings (Settings class)
│   │   ├── main.py             # FastAPI app entry
│   │   ├── database.py         # Async SQLAlchemy session
│   │   ├── kiwoom_client/
│   │   │   ├── auth.py         # B-3: Token management
│   │   │   ├── market.py       # B-4: 시세 클라이언트
│   │   │   ├── order.py        # B-5: 주문 클라이언트
│   │   │   └── account.py      # B-6: 계좌 클라이언트
│   │   ├── core/
│   │   │   ├── news_client.py  # B-11/B-12: StockNews REST+Redis
│   │   │   ├── market_data.py  # B-7: 시세 수집, VWAP/캔들
│   │   │   ├── scanner.py      # B-10: Opening Scanner
│   │   │   ├── strategy.py     # B-13: Strategy Engine
│   │   │   ├── risk.py         # B-14: Risk Management
│   │   │   ├── order_executor.py # B-15: 분할매수/재시도
│   │   │   ├── trader.py       # B-8: 자동매매 루프
│   │   │   ├── learning.py     # B-19: 성과 분석
│   │   │   ├── report.py       # B-20: 자동 리포트
│   │   │   └── tuner.py        # B-21: 파라미터 튜닝
│   │   ├── api/
│   │   │   ├── account.py      # B-9: 계좌 API
│   │   │   ├── trades.py       # B-16: 매매 내역 API
│   │   │   ├── scanner.py      # B-10: Scanner API
│   │   │   ├── reports.py      # B-22: 리포트 API
│   │   │   ├── strategy.py     # B-17: 전략 관리 API
│   │   │   └── ws.py           # B-18: WebSocket 실시간
│   │   └── models/
│   │       ├── db_models.py    # B-2: 4 ORM models
│   │       └── schemas.py      # B-2: Pydantic schemas
│   └── tests/                  # 145 tests (97.59% coverage)
│       ├── test_setup.py
│       └── unit/
│           ├── kiwoom_client/  # auth, market, order, account
│           ├── core/           # market_data, scanner, strategy, risk, order_executor, trader, learning, report, tuner, news
│           ├── api/            # account, trades, reports, scanner, strategy, websocket
│           └── models/         # db_models, schemas
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/
│   │   │   ├── Navigation.tsx  # F-1: Sidebar nav
│   │   │   ├── AuthSettings.tsx # F-3: 인증 UI
│   │   │   ├── Dashboard.tsx   # F-4: 계좌 대시보드
│   │   │   ├── PositionList.tsx # F-5: 포지션 현황
│   │   │   ├── SystemStatus.tsx # F-6: WebSocket 상태
│   │   │   ├── TradesPage.tsx  # F-7: 매매 내역
│   │   │   ├── StrategyPage.tsx # F-8: 전략 설정
│   │   │   ├── ScannerPage.tsx # F-9: 스캐너 뷰
│   │   │   ├── RiskSettings.tsx # F-10: 리스크 설정
│   │   │   ├── OrderMonitor.tsx # F-11: 주문 모니터
│   │   │   ├── ProfitChart.tsx # F-12: 성과 차트
│   │   │   ├── MetricsDashboard.tsx # F-13: 학습 메트릭
│   │   │   └── ReportViewer.tsx # F-14: 리포트 뷰어
│   │   ├── lib/
│   │   │   ├── api.ts          # API client (12 methods)
│   │   │   └── types.ts        # Shared types (12 interfaces)
│   │   └── mocks/
│   │       ├── handlers.ts     # MSW handlers (14 routes)
│   │       └── server.ts       # MSW test server
│   └── tests/                  # 64 tests, 14 suites (93.52% lines)
│       ├── jest-env-jsdom.ts   # Custom Jest env (Node 24 compat)
│       ├── setup.ts            # Jest setup
│       ├── setup.test.tsx
│       ├── unit/components/    # 12 component test files
│       └── integration/
│           └── api-client.test.ts
├── docker-compose.yml          # PostgreSQL + Redis
├── docs/
│   ├── StockAgent-v1.0.md      # Design spec (source of truth)
│   ├── StockAgent_Task.md      # Execution plan
│   ├── TestAgent.md            # TDD test plan
│   └── err/                    # Error logs per task
└── CLAUDE.md
```

## Development Progress

| Sprint | Tasks | Status |
|--------|-------|--------|
| 0 | B-1, F-1, F-2 | ✅ Complete |
| 1 | B-2, B-3, B-11 | ✅ Complete |
| 2 | B-4~B-6, B-9, B-12, B-14, B-19, F-3~F-5 | ✅ Complete |
| 3 | B-7, B-15, B-16, B-20, F-6, F-7, F-10 | ✅ Complete |
| 4 | B-8, B-10, B-22, F-8, F-9, F-11 | ✅ Complete |
| 5 | B-13, B-18, F-12, F-13, F-14 | ✅ Complete |
| 6 | B-17, B-21 | ✅ Complete |

Backend: 145 tests passing (97.59% coverage) | Frontend: 64 tests passing, 14 suites (93.52% line coverage)

### Test Coverage Details

**Backend (97.59%):**
- 100%: api/* (6), config, main, models/* (3), kiwoom_client/* (4), core/market_data, report, scanner, strategy, tuner
- 95%+: core/learning (97%), risk (97%), news_subscriber (95%), order_executor (98%)
- 90%+: core/trader (93%), news_client (90%)
- Excluded: database.py (DB infra, 0%)

**Frontend (93.52% lines):**
- Components 평균 97.18% lines (6개 100%, 나머지 94%+)
- lib/api.ts 96.42%, mocks 100%
- app/* page stubs 제외 (라우터 진입점)

## Key Design Decisions

- **jest.config.ts**: `createJestConfig` result patched post-resolution for `transformIgnorePatterns` (MSW ESM compat)
- **Custom Jest environment**: `tests/jest-env-jsdom.ts` extends JSDOMEnvironment to copy Node 24 Web API globals (fetch, ReadableStream, MessagePort, etc.) into jsdom sandbox for MSW v2 compatibility
- **API client tests**: use `@jest-environment node` (no DOM needed, avoids fetch polyfill)
- **respx fixtures**: use `assert_all_called=False` when tests override routes
- **Pydantic schemas**: `Field` constraints for validation (ge=0, min_length=1, date pattern)
- **WebSocket Mock**: Custom mock pattern (no jest-websocket-mock) - replace global.WebSocket with jest.fn() returning mock object
- **Strategy Engine**: All 4 conditions (volume_rank, news_score, VWAP, opening_high) must be met for buy signal
- **Parameter Tuner**: Uses median for top_n, 25th percentile for news_threshold (conservative approach)
