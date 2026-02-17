# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StockNews is a **News Intelligence Service** (뉴스 수집/분석 시스템) that collects, processes, and scores financial news for Korean and US stock markets. It operates independently from the StockAgent trading system and exposes data via REST API and Redis Pub/Sub.

The design specifications are in `docs/` (written in Korean):
- `docs/StockNews-v1.0.md` — **current** full-stack design (Frontend + Backend)
- `docs/StockNews_Task.md` — development task plan with parallel execution mapping
- `docs/TestAgent.md` — TDD-based test sub-agent specification

## Tech Stack

### Backend
- **Language:** Python 3.12+ (dev: 3.13)
- **Web Framework:** FastAPI
- **Database:** PostgreSQL (production) / SQLite (MVP)
- **ORM:** SQLAlchemy 2.0
- **Cache/Pub-Sub:** Redis 7+
- **Scheduling:** APScheduler
- **NLP:** OpenAI/LLM API for summarization and sentiment; KoNLPy or regex for stock code mapping

### Frontend
- **Language:** TypeScript 5+
- **UI Framework:** React 18
- **Build:** Vite 5+
- **Server State:** TanStack Query v5
- **Charts:** Recharts
- **Styling:** Tailwind CSS 3
- **Routing:** React Router v6

## Architecture

```
Frontend (React) ── REST / WebSocket ──┐
                                       │
                              Backend (FastAPI)
                                       │
External Sources (Naver, DART, RSS) ───┘
  → News Collector (batch + near-realtime)
  → Preprocessing & Deduplication
  → LLM/NLP Analysis (stock mapping, theme classification, sentiment)
  → News Scoring Engine (Recency 0.4 + Frequency 0.3 + Sentiment 0.2 + Disclosure 0.1)
  → News Database (PostgreSQL/SQLite)
  → REST API + WebSocket → Frontend Dashboard
  → Redis Pub/Sub → StockAgent-KR / StockAgent-US
```

## Key API Endpoints

- `GET /news/score?stock={code}` — news score for a stock
- `GET /news/top?market={KR|US}` — top scored news by market
- `GET /news/latest` — latest news list (paginated)
- `GET /stocks/{code}/timeline` — score timeline for a stock
- `GET /theme/strength` — theme strength rankings
- `GET /health` — server health check
- `WS /ws/news` — real-time breaking news stream

## Database Tables

- **news_event** — individual news items with stock code, theme, sentiment, score, source
- **theme_strength** — daily aggregated theme metrics

## Project Structure

```
StockNews/
├── backend/          # FastAPI server (Python)
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── collectors/   # News collection modules
│   │   ├── processing/   # NLP/analysis pipeline
│   │   ├── scoring/      # Scoring engine
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── core/         # Config, DB, Redis
│   └── tests/
├── frontend/         # React dashboard (TypeScript)
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── api/          # API client
│   │   └── types/        # TypeScript types
│   └── tests/
└── docs/
```

## Development Status

This project has a **completed v1.0 design specification** (`docs/StockNews-v1.0.md`) covering both Frontend and Backend. No application code has been written yet. Development follows a phased approach:

- **Phase 1 (MVP):** Korean news collection (Naver + DART) → Scoring → REST API → React dashboard
- **Phase 2:** US market expansion (Finnhub/NewsAPI), LLM accuracy improvements, real-time enhancements
- **Phase 3:** AI-based news impact prediction model

See Section 9 of the v1.0 spec for the detailed task dependency graph.
