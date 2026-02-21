# StockNews Project Status Report

> Last Updated: 2026-02-21
> CI Run: [#22252889845](https://github.com/redstarh/stock-agent/actions/runs/22252889845) — **ALL GREEN**

---

## 1. Project Overview

StockNews는 한국/미국 주식 시장의 뉴스를 수집, 분석, 스코어링하는 News Intelligence Service입니다.

| Item | Detail |
|------|--------|
| Repository | `redstarh/stock-agent` (monorepo: `StockNews/`) |
| Backend | Python 3.13 / FastAPI / SQLAlchemy 2.0 |
| Frontend | React 19 / TypeScript / Vite / Tailwind CSS 4 |
| Database | SQLite (MVP) / PostgreSQL (production) |
| Cache | Redis 7+ |
| CI/CD | GitHub Actions (4 jobs) |

---

## 2. Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Korean news (Naver + DART) + Scoring + REST API + Dashboard | Complete |
| Phase 2 | US market (Finnhub/NewsAPI) + LLM sentiment + Summary | Complete |
| Phase 3 | AI prediction (Random Forest) + Prediction API + Dashboard | Complete |
| Phase 4 | Verification engine + Training data pipeline (53 files) | Complete |
| ML Pipeline | 5-phase ML pipeline (yfinance, model registry, SHAP, Optuna) | Complete |
| Production | Monitoring, security, CI/CD, Docker, logging | Complete |
| Advan | 이벤트 기반 휴리스틱 예측 시스템 (v1/v2) + 시뮬레이션 엔진 | Complete |

---

## 3. CI/CD Pipeline

### Workflow: `.github/workflows/test.yml`

```
backend-test ──────────────┐
                           ├──> docker-build
frontend-unit-test ────────┘
       │
       └──> frontend-e2e-test
```

### Jobs

| Job | Steps | Duration |
|-----|-------|----------|
| **backend-test** | Checkout → Python 3.13 → pip install → ruff check → pytest --cov → Upload coverage | ~2m30s |
| **frontend-unit-test** | Checkout → Node 20 → npm ci → eslint → tsc -b → vitest --coverage → Upload coverage | ~1m30s |
| **frontend-e2e-test** | Checkout → Node 20 → npm ci → Playwright install → Playwright test → Upload report | ~1m45s |
| **docker-build** | Checkout → Docker Buildx → Build backend image → Build frontend image | ~4m |

### Latest CI Result (Manual Dispatch #22252889845)

| Job | Status |
|-----|--------|
| backend-test | PASS |
| frontend-unit-test | PASS |
| frontend-e2e-test | PASS |
| docker-build | PASS |

---

## 4. Test Coverage

| Area | Framework | Tests | Status |
|------|-----------|-------|--------|
| Backend unit/integration | pytest | 570 passed | PASS |
| Frontend unit | vitest | 200 | PASS |
| Frontend E2E | Playwright | 18 | PASS |
| **Total** | | **788+** | **PASS** |

Backend coverage: **87.48%** (threshold: 80%)

> Note: Backend test count decreased from 651 to 570 due to Advan system refactoring (removed deprecated simulation/prediction tests, added new Advan-specific tests). Frontend tests increased from 196 to 200 with new Advan verification and comparison page tests.

---

## 5. Production Readiness Checklist

### Infrastructure

| # | Task | Details | Status |
|---|------|---------|--------|
| 1 | Dockerfiles | Backend + Frontend multi-stage builds | Done |
| 2 | Docker Compose | 8 services (backend, frontend, db, redis, prometheus, grafana) | Done |
| 3 | Alembic migrations | Database schema versioning | Done |
| 4 | Health checks | `/health` endpoint (DB + Redis connectivity) | Done |
| 5 | Structured logging | structlog JSON + request correlation middleware | Done |
| 6 | Log aggregation | json-file rotation + optional Fluentd/ELK | Done |

### Monitoring & Alerting

| # | Task | Details | Status |
|---|------|---------|--------|
| 7 | Sentry | Error tracking with sanitized exception messages | Done |
| 8 | Prometheus | `/metrics` endpoint via prometheus-fastapi-instrumentator | Done |
| 9 | Grafana dashboards | 7 panels (request rate, error rate, latency percentiles, etc.) | Done |
| 10 | Alerting rules | 4 rules (HighErrorRate, HighLatency, ServiceDown, HighMemory) | Done |

### Security

| # | Task | Details | Status |
|---|------|---------|--------|
| 11 | API authentication | API Key + optional JWT, development mode bypass | Done |
| 12 | CORS hardening | Restricted methods/headers (GET/POST/PUT/DELETE/OPTIONS) | Done |
| 13 | Rate limiting | slowapi (60/min per endpoint) | Done |
| 14 | API key rotation | Dual-key support (current + next) with audit logging | Done |
| 15 | PostgreSQL SSL | Configurable ssl_mode (require/verify-ca/verify-full) | Done |
| 16 | Redis AUTH + TLS | Password auth + optional SSL/TLS context | Done |
| 17 | Secrets manager | 3 providers (ENV, File, AWS Secrets Manager) | Done |

### API & Integration

| # | Task | Details | Status |
|---|------|---------|--------|
| 18 | API versioning v2 | `/api/v1/` (deprecated) + `/api/v2/` (stable) + `/api/versions` | Done |
| 19 | Deprecation headers | RFC 8594 Deprecation + Sunset + Link headers on v1 | Done |
| 20 | Redis message validation | Pydantic schemas (BreakingNewsMessage, ScoreUpdateMessage) | Done |
| 21 | Contract tests | Cross-project REST + Redis Pub/Sub contract v1.1 | Done |
| 22 | CI/CD pipeline | 4-job GitHub Actions (lint, test, e2e, docker) | Done |

---

## 6. Commit Log

Total: **44 commits** | **185 files changed** | **+23,639 lines**

### Feature Commits

| Hash | Date | Description |
|------|------|-------------|
| `53b22b8` | 2026-02-21 | feat: add API versioning v2 strategy and secrets manager integration |
| `f01c09e` | 2026-02-21 | feat: add production monitoring, security hardening, and message validation |
| `81a50fc` | 2026-02-21 | feat: cross-project contract tests + contract v1.1 update |
| `8bab5c6` | 2026-02-21 | feat: structured JSON logging with request correlation middleware |
| `3805c03` | 2026-02-21 | feat: production Docker setup, CI/CD pipelines, PostgreSQL support |
| `43bb515` | 2026-02-21 | feat: ML Pipeline Phase 4 — SHAP feature selection, Optuna tuning, auto-rollback |
| `37a65a4` | 2026-02-21 | feat: ML Pipeline Phase 3 — Tier 3 columns, extended API, ML Dashboard frontend |
| `d2c52db` | 2026-02-20 | feat: ML Pipeline Phase 2 — Tier 2 expansion, model registry, cross-theme scoring |
| `af17eb0` | 2026-02-20 | feat: ML Pipeline Phase 1 — Tier 1 model, feature config, market indicators |
| `db11d5a` | 2026-02-20 | feat: ML Pipeline Phase 0 — yfinance resilience, backfill endpoint, validator |
| `ca5ce88` | 2026-02-20 | feat: add Sentry error tracking, Prometheus metrics, API auth, CORS, rate limiting |
| `8985783` | 2026-02-20 | feat: prediction verification engine + ML training data pipeline |
| `3e0307e` | 2026-02-19 | feat: persist market selection across page navigation via React Context |
| `d7d50a7` | 2026-02-19 | feat: cross-market analysis, LLM theme classifier, prediction scores, sentiment fix |
| `7ba1d14` | 2026-02-18 | fix: correct WebSocket URL port from 8000 to 8001 |
| `019b96b` | 2026-02-18 | feat: multi-model Bedrock parallel pipeline + frontend enhancements |
| `66912e0` | 2026-02-18 | feat: add AWS SSO profile support for Bedrock client |

### CI/Fix Commits

| Hash | Date | Description |
|------|------|-------------|
| `7ffd4b9` | 2026-02-21 | fix: use isolated test app for versioning header tests |
| `39931b1` | 2026-02-21 | fix: add raise_server_exceptions=False to versioning tests for CI |
| `271f74d` | 2026-02-21 | ci: add workflow_dispatch trigger for manual CI runs |
| `0413e0f` | 2026-02-21 | fix: resolve CI test failures (auth DB error, optional ML deps) |
| `6192213` | 2026-02-21 | fix: add missing CI dependencies and adjust coverage thresholds |
| `711be21` | 2026-02-21 | fix: resolve all CI lint errors (ruff + eslint) |
| `88ed161` | 2026-02-21 | fix: update CI workflow paths for monorepo structure |

---

## 7. Architecture

```
Frontend (React 19 + Vite)
  │
  ├── REST API (/api/v1, /api/v2)
  ├── WebSocket (/ws/news)
  └── Dashboard (News, Stocks, Themes, Predictions, Verification (Advan), 예측 비교)
      • All pages: date filtering support
      • Verification: date-specific accuracy display

Backend (FastAPI)
  │
  ├── Collectors (Naver, DART, Finnhub, NewsAPI)
  ├── Processing (NLP, Sentiment, Theme Classification)
  ├── Scoring Engine (Recency 0.4 + Frequency 0.3 + Sentiment 0.2 + Disclosure 0.1)
  ├── ML Pipeline (Random Forest, SHAP, Optuna, Model Registry)
  ├── Advan System (Event Extraction → Heuristic Prediction → Labeling → Verification)
  ├── Verification Engine (Prediction tracking + Price fetching)
  ├── Training Pipeline (Feature builder + Backfill)
  │
  ├── PostgreSQL / SQLite (news_event, theme_strength, predictions, training)
  ├── Redis (Cache + Pub/Sub → StockAgent)
  │
  ├── Monitoring (Prometheus + Grafana + Sentry)
  └── Security (API Key + Rate Limit + CORS + SSL/TLS)

External Consumers
  └── StockAgent (REST API + Redis Pub/Sub subscriber)
```

---

## 8. Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/news/score?stock={code}` | News score for a stock |
| GET | `/api/v2/news/top?market={KR\|US}&date={YYYY-MM-DD}` | Top scored news by market (date optional) |
| GET | `/api/v2/news/latest` | Latest news (paginated, filterable) |
| GET | `/api/v2/stocks/{code}/timeline` | Score timeline for a stock |
| GET | `/api/v2/themes/strength?date={YYYY-MM-DD}` | Theme strength rankings (date optional) |
| GET | `/api/versions` | Available API versions |
| GET | `/health` | Server health (DB + Redis) |
| GET | `/metrics` | Prometheus metrics |
| WS | `/ws/news` | Real-time breaking news |

---

## 9. Configuration Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./stocknews.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `API_KEY` | Current API authentication key | `dev-api-key-change-in-production` |
| `API_KEY_NEXT` | Next rotation key (optional) | `` |
| `REQUIRE_AUTH` | Enable API authentication | `false` |
| `SENTRY_DSN` | Sentry error tracking DSN | `` |
| `SECRETS_PROVIDER` | Secrets source (`""`/`aws`/`file`) | `` |
| `SECRETS_NAME` | AWS SM secret name or JSON path | `` |
| `APP_ENV` | Environment (`development`/`production`) | `development` |
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` |

Full reference: `backend/.env.example`

---

## 10. Running Locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --port 8001 --reload

# Frontend
cd frontend
npm install
npm run dev

# Docker (all services)
docker compose up -d
# Access: Frontend :5173 | Backend :8001 | Grafana :3000 | Prometheus :9090
```
