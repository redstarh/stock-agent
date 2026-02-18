# CLAUDE.md — StockPlatform Manager

This file provides guidance to Claude Code when working across the StockNews and StockAgent projects.

## Platform Overview

StockPlatform is a two-system architecture for Korean/US stock market news analysis and automated trading.

```
StockNews (뉴스 수집/분석)          StockAgent (자동매매)
  Port 8001                          Port 8000
  ┌─────────────┐                   ┌─────────────┐
  │ Naver/DART  │                   │ Kiwoom REST │
  │ Finnhub     │──REST API────────►│ Strategy    │
  │ NewsAPI     │──Redis Pub/Sub───►│ Risk Mgmt   │
  │ LLM/NLP    │                   │ Order Exec  │
  └─────────────┘                   └─────────────┘
```

| System | Path | Role | Status |
|--------|------|------|--------|
| **StockNews** | `~/AgentDev/StockNews` | News collection, scoring, analysis, prediction | Phase 1-3 complete |
| **StockAgent** | `~/AgentDev/StockAgent` | Automated trading with Kiwoom REST API | Sprint 0-6 complete |
| **Shared** | `~/AgentDev/shared/` | Integration contracts, cross-project configs | Active |

## Cross-Project Manager Role

When working in `~/AgentDev/`, you act as the **StockPlatformManager** — a technical program manager overseeing both systems. Follow these rules:

### Scope Detection

| User Request Pattern | Target | Action |
|---------------------|--------|--------|
| "뉴스", "수집", "스코어링", "감성" | StockNews | `cd StockNews` and work there |
| "매매", "전략", "주문", "키움", "포지션" | StockAgent | `cd StockAgent` and work there |
| "통합", "연동", "배포", "인프라", "둘 다" | Cross-project | Orchestrate both |
| "상태", "진행", "현황" | Platform-wide | Report both projects |

### Priority Rules

1. **API 계약 변경** → StockNews 먼저 (provider-first principle)
2. **Redis 스키마 변경** → 양쪽 동시 업데이트 (coordinated release)
3. **독립 기능** → 병렬 실행 (ultrawork)
4. **배포** → StockNews 배포 → StockAgent 배포 순서
5. **장애** → StockAgent 우선 (금전적 영향이 큼)

### Agent Routing

| Task Domain | Agent | Tier | Notes |
|-------------|-------|------|-------|
| StockNews backend | `executor` | Sonnet | Python/FastAPI |
| StockNews frontend | `designer` | Sonnet | React/Vite/Tailwind |
| StockAgent backend | `executor` | Sonnet | Python/FastAPI |
| StockAgent frontend | `designer` | Sonnet | Next.js/React |
| NLP/ML pipeline | `executor-high` | Opus | Sentiment, prediction models |
| Trading strategy | `executor-high` | Opus | Risk, order execution |
| Cross-project integration | `qa-tester-high` | Opus | Redis + REST 연동 |
| Infrastructure (Docker, K8s) | `executor-high` | Opus | Dockerfiles, CI/CD |
| Architecture decisions | `architect` | Opus | DB migration, scaling |
| Sprint planning | `planner` | Opus | Priority, dependency |
| Plan review | `critic` | Opus | Design critique |
| Data analysis | `scientist` | Sonnet | Backtest, correlation |
| Security review | `security-reviewer` | Opus | API keys, auth |
| Code review | `code-reviewer` | Opus | Quality gates |
| Documentation | `writer` | Haiku | API docs, guides |
| Git operations | `git-master` | Sonnet | Commits, tags, PRs |
| Quick fixes | `executor-low` | Haiku | Typos, simple changes |
| Quick search | `explore` | Haiku | File/code lookup |

### Verification Protocol

Before claiming any cross-project work is complete, run:

```bash
# StockNews
cd ~/AgentDev/StockNews/backend && .venv/bin/python -m pytest -q
cd ~/AgentDev/StockNews/frontend && npx tsc -b && npx vitest run

# StockAgent
cd ~/AgentDev/StockAgent/backend && .venv/bin/python -m pytest -q
cd ~/AgentDev/StockAgent/frontend && npm test
```

For integration verification, both services must be running.

## Integration Contracts

Contracts are defined in `~/AgentDev/shared/contracts/`. These are the **source of truth** for inter-system communication.

### REST API Contract

**Provider:** StockNews (port 8001)
**Consumer:** StockAgent (`backend/src/core/news_client.py`)

```
GET /api/v1/news/score?stock={code}
→ { stock_code, stock_name, news_score (0-100), recency, frequency, sentiment_score, disclosure, news_count }

GET /api/v1/news/top?market={KR|US}&limit=10
→ [{ stock_code, stock_name, news_score, sentiment, news_count, market }]
```

**Rules:**
- StockNews MUST maintain backward compatibility on these endpoints
- New fields can be added; existing fields MUST NOT be removed or renamed
- Response time target: < 200ms (cached), < 2s (uncached)

### Redis Pub/Sub Contract

**Publisher:** StockNews (`app/core/pubsub.py`)
**Subscriber:** StockAgent (`backend/src/core/news_subscriber.py`)

```
Channel: breaking_news
Payload: {
  "type": "breaking_news",
  "stock_code": "005930",
  "title": "삼성전자 4분기 실적 발표",
  "score": 85.5,        // 0-100
  "sentiment": 0.8,     // -1.0 ~ 1.0
  "market": "KR"        // "KR" | "US"
}
```

**Rules:**
- Threshold: score >= 80.0 triggers breaking news
- Message format changes require version bump in `shared/contracts/redis-messages.json`
- StockAgent MUST handle unknown fields gracefully (ignore, don't crash)

## Tech Stack Summary

| Component | StockNews | StockAgent |
|-----------|-----------|------------|
| Python | 3.13 | 3.13 |
| Backend | FastAPI | FastAPI |
| ORM | SQLAlchemy 2.0 (sync) | SQLAlchemy 2.0 (async) |
| DB | SQLite (MVP) / PostgreSQL | PostgreSQL |
| Cache | Redis 7+ | Redis 7+ |
| Frontend | React 19 + Vite | Next.js 16 + React 19 |
| CSS | Tailwind CSS 4 | TailwindCSS v4 |
| State | TanStack Query v5 | TanStack Query v5 |
| Charts | Recharts | Recharts |
| Test (BE) | pytest + respx + fakeredis | pytest + respx + fakeredis |
| Test (FE) | Vitest + Playwright | Jest + RTL |
| CI/CD | GitHub Actions | GitHub Actions |

## Test Counts (Latest)

| Project | Backend | Frontend Unit | Frontend E2E | Total |
|---------|---------|--------------|-------------|-------|
| StockNews | 192 (1 skip) | 110 | 18 | 320 |
| StockAgent | 145 | 64 | — | 209 |
| **Platform** | **337** | **174** | **18** | **529** |

## Project Paths

| Resource | StockNews | StockAgent |
|----------|-----------|------------|
| Backend src | `StockNews/backend/app/` | `StockAgent/backend/src/` |
| Frontend src | `StockNews/frontend/src/` | `StockAgent/frontend/src/` |
| Backend tests | `StockNews/backend/tests/` | `StockAgent/backend/tests/` |
| Frontend tests | `StockNews/frontend/tests/` | `StockAgent/frontend/tests/` |
| Design docs | `StockNews/docs/` | `StockAgent/docs/` |
| Python venv | `StockNews/backend/.venv/` | `StockAgent/backend/.venv/` |
| CLAUDE.md | `StockNews/CLAUDE.md` | `StockAgent/CLAUDE.md` |

## Next Steps (Recommended)

### Production Readiness (Both)
- [ ] Dockerfiles for backend and frontend
- [ ] Alembic migration setup (StockNews)
- [ ] Docker Compose (integrated — both services + PostgreSQL + Redis)
- [ ] Rate limiting middleware
- [ ] Health check endpoints (DB + Redis connectivity)
- [ ] Logging aggregation setup

### Integration Hardening
- [ ] Cross-project integration test suite
- [ ] Contract testing (consumer-driven)
- [ ] Redis message schema validation
- [ ] API versioning strategy (v2 planning)

### Monitoring & Operations
- [ ] Prometheus metrics endpoints
- [ ] Grafana dashboards (trading P&L, news throughput)
- [ ] Error tracking (Sentry)
- [ ] Alerting rules (trade failures, news collection gaps)

### Security
- [ ] API key rotation mechanism
- [ ] JWT authentication for StockAgent admin
- [ ] Redis AUTH + TLS
- [ ] PostgreSQL SSL connections
- [ ] Secrets manager integration
