# StockNews Documentation

Welcome to the StockNews documentation directory. This guide helps you navigate and understand the available documentation for the News Intelligence Service.

---

## Quick Navigation

**New to StockNews?** Start with [PRD.md](./PRD.md) for the product overview, then [ARCHITECTURE.md](./ARCHITECTURE.md) for system design.

**Looking for current status?** See [PROJECT_STATUS.md](./PROJECT_STATUS.md).

**Need to understand system behavior?** Use [SYSTEM_FLOW.md](./SYSTEM_FLOW.md) for high-level flows and [DETAILED_FLOWS.md](./DETAILED_FLOWS.md) for component-level details.

---

## Core Documentation (Active)

These documents describe the current production system (Phase 1-3 complete).

| Document | Purpose | Audience | Key Sections |
|----------|---------|----------|--------------|
| **[PRD.md](./PRD.md)** | Product Requirements Document | Product managers, stakeholders | Vision, goals, requirements, KPIs, phases |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | System Architecture | Backend engineers, architects | Tech stack, data model, API design, ML pipeline, security, deployment |
| **[SYSTEM_FLOW.md](./SYSTEM_FLOW.md)** | High-Level Data Flows | All engineers | Collection, processing, scoring, distribution, ML, frontend flows |
| **[DETAILED_FLOWS.md](./DETAILED_FLOWS.md)** | Component-Level Technical Flows | Backend engineers | News collection, processing pipeline, scoring engine, API handling, WebSocket, ML training |
| **[DEVELOPMENT_HISTORY.md](./DEVELOPMENT_HISTORY.md)** | Development Timeline | Project leads, contributors | Phase breakdown, commits, test evolution, team contributions |
| **[PROJECT_STATUS.md](./PROJECT_STATUS.md)** | Current Status & CI Results | All developers | Phase status, test counts, build results, recent commits, known issues |

---

## Document Relationships & Reading Paths

### For Different Roles

**Product Owner / Stakeholder:**
1. [PRD.md](./PRD.md) — Understand the product vision and key metrics
2. [PROJECT_STATUS.md](./PROJECT_STATUS.md) — Review current progress

**Backend Engineer (New Contributor):**
1. [PRD.md](./PRD.md) § 1-2 — Product context
2. [ARCHITECTURE.md](./ARCHITECTURE.md) — System design
3. [DETAILED_FLOWS.md](./DETAILED_FLOWS.md) — Implementation details
4. Source code in `backend/app/`

**Frontend Engineer (New Contributor):**
1. [PRD.md](./PRD.md) § 5 — Frontend requirements
2. [SYSTEM_FLOW.md](./SYSTEM_FLOW.md) § 7 — Frontend interaction flow
3. [ARCHITECTURE.md](./ARCHITECTURE.md) § 4 — API contracts
4. Source code in `frontend/src/`

**ML Engineer / Data Scientist:**
1. [ARCHITECTURE.md](./ARCHITECTURE.md) § 5 — ML pipeline architecture
2. [DETAILED_FLOWS.md](./DETAILED_FLOWS.md) § 6 — ML training flow
3. [DEVELOPMENT_HISTORY.md](./DEVELOPMENT_HISTORY.md) — ML pipeline phases
4. Source code in `backend/app/ml/`

**DevOps / SRE:**
1. [ARCHITECTURE.md](./ARCHITECTURE.md) § 6-7 — Deployment and security
2. [PROJECT_STATUS.md](./PROJECT_STATUS.md) — CI/CD results
3. Dockerfiles and GitHub Actions in `backend/` and `frontend/`

### For Specific Tasks

**Understanding a bug or incident:**
1. [PROJECT_STATUS.md](./PROJECT_STATUS.md) § 5 — Known issues
2. [DETAILED_FLOWS.md](./DETAILED_FLOWS.md) — Component flows (find the area)
3. Source code + logs

**Integrating with StockAgent:**
1. [ARCHITECTURE.md](./ARCHITECTURE.md) § 8 — Integration architecture
2. [SYSTEM_FLOW.md](./SYSTEM_FLOW.md) § 5 — Distribution flow
3. API endpoints in `backend/app/api/`

**Planning a new feature:**
1. [PRD.md](./PRD.md) — Existing feature scope
2. [ARCHITECTURE.md](./ARCHITECTURE.md) — System design patterns
3. [SYSTEM_FLOW.md](./SYSTEM_FLOW.md) — Identify integration points
4. [DEVELOPMENT_HISTORY.md](./DEVELOPMENT_HISTORY.md) — Phase planning patterns

---

## Document Details

### PRD.md
- **Lines:** ~630
- **Content:** Executive summary, vision, strategic goals, business objectives, feature scope, API specification, database schema, testing strategy, deployment plan
- **Currency:** Updated 2026-02-21
- **Use when:** You need to understand WHAT we're building and WHY

### ARCHITECTURE.md
- **Lines:** ~1,300
- **Content:** Technology stack, data architecture, API architecture, ML pipeline, deployment (Docker/K8s), security (auth, secrets, SSL), integration points
- **Currency:** Updated 2026-02-21
- **Use when:** You need to understand HOW the system is structured

### SYSTEM_FLOW.md
- **Lines:** ~1,600
- **Content:** High-level flows for all major subsystems with ASCII diagrams and explanations
- **Flows covered:**
  - Data collection (Naver, DART, Finnhub, NewsAPI)
  - Processing and deduplication
  - Scoring engine
  - Distribution (API, Pub/Sub, WebSocket)
  - ML prediction pipeline
  - Frontend interaction
- **Currency:** Updated 2026-02-21
- **Use when:** You want a bird's-eye view of how data moves through the system

### DETAILED_FLOWS.md
- **Lines:** ~1,500
- **Content:** Component-level technical flows with step-by-step breakdowns, code references, and decision points
- **Flows covered:**
  - News collection (Naver, DART, Finnhub, NewsAPI)
  - Processing pipeline (dedup, tag extraction, NLP)
  - Scoring engine (recency, frequency, sentiment, disclosure)
  - API request handling and response
  - WebSocket broadcasting
  - ML training loop
- **Currency:** Updated 2026-02-21
- **Use when:** You need to understand exactly how a specific component works and find the relevant source files

### DEVELOPMENT_HISTORY.md
- **Lines:** ~650
- **Content:** Phase-by-phase development timeline with commit counts, test evolution, team contributions, and learning outcomes
- **Phases documented:** Phase 0-4 (setup, MVP, US market, predictions, verification)
- **Currency:** Updated 2026-02-21
- **Use when:** You want to understand how the project evolved and learn from past decisions

### PROJECT_STATUS.md
- **Lines:** ~300
- **Content:** Current phase status, test counts, CI/CD results, recent commits, known issues, next steps
- **Sections:** Phases, test counts, CI results, dependencies, blockers, recent work
- **Currency:** Updated 2026-02-21 (auto-updated on releases)
- **Use when:** You want a quick status check or to find what's currently broken/in-progress

---

## Archived Documentation

These documents are preserved for reference and historical context but are **not actively maintained**. They may contain outdated information.

### archived/v1-legacy/
Original design documents from the project inception. Kept for historical reference.

| Document | Purpose |
|----------|---------|
| **StockNews-v1.0.md** | Original full-stack design document |
| **CONSOLIDATED_SUMMARY.md** | Executive summary of v1 design |
| **ARCHIVE_CANDIDATES.md** | Decision log on what to archive |

### archived/specs/
Detailed feature specifications that have been implemented.

| Document | Coverage |
|----------|----------|
| **MLPipeline-Spec.md** | Random Forest model and feature engineering spec |
| **PredictionVerification-Spec.md** | Prediction verification engine specification |
| **PredictionVerification-Architecture.md** | Architecture for prediction backtesting |
| **PredictionVerification-TestPlan.md** | Test plan for verification system |

### archived/task-plans/
Development task breakdowns used during implementation. Kept for process reference.

| Document | Purpose |
|----------|---------|
| **StockNews_Task.md** | Complete task list with parallel execution mapping |
| **TestAgent.md** | TDD-based test sub-agent specification |

### archived/err/
Historical error logs and incident reports from development phases.

| Logs | Purpose |
|------|---------|
| **Task*.err.md** | Development errors and resolutions (Tasks 1-13) |

---

## Document Maintenance Guide

### When to Update Each Document

| Document | Update Trigger | Frequency |
|----------|----------------|-----------|
| **PRD.md** | New feature requirement, requirement change | Per sprint |
| **ARCHITECTURE.md** | Tech stack change, major refactor, new component | Per phase |
| **SYSTEM_FLOW.md** | New data flow, process change | Per phase |
| **DETAILED_FLOWS.md** | Component refactor, new API endpoint | Per sprint |
| **DEVELOPMENT_HISTORY.md** | Phase completion, major milestone | Per phase |
| **PROJECT_STATUS.md** | Test failure, blocker, recent commit | Weekly / per incident |

### Versioning Strategy

- **PRD.md & ARCHITECTURE.md:** Major version (e.g., 1.0 → 2.0) on breaking changes; minor version on additions
- **SYSTEM_FLOW.md & DETAILED_FLOWS.md:** Tracked by last-updated date; no explicit versioning
- **DEVELOPMENT_HISTORY.md:** Append-only; never modify past entries
- **PROJECT_STATUS.md:** "Last Updated" field; CI run link for verification

### Update Checklist

Before marking a document as "updated":

- [ ] Verify the content matches current source code
- [ ] Update the "Last Updated" date (YYYY-MM-DD format)
- [ ] Test any code examples or commands included
- [ ] Review for outdated links or references
- [ ] Update related documents if there are cascading changes
- [ ] Create a git commit with clear message: `docs: update [DOCUMENT] for [REASON]`

---

## Quick Reference: File Locations

```
docs/
├── README.md                    (you are here)
├── PRD.md                       (product requirements)
├── ARCHITECTURE.md              (system architecture)
├── SYSTEM_FLOW.md               (high-level flows)
├── DETAILED_FLOWS.md            (component flows)
├── DEVELOPMENT_HISTORY.md       (timeline & evolution)
├── PROJECT_STATUS.md            (current status)
├── archived/
│   ├── README.md                (archive guide)
│   ├── v1-legacy/               (original design)
│   ├── specs/                   (feature specs)
│   ├── task-plans/              (task breakdowns)
│   └── err/                     (error logs)
└── .omc/                        (internal state)
```

---

## Frequently Asked Questions

**Q: Which document should I read first?**
A: Start with [PRD.md](./PRD.md) for context, then [ARCHITECTURE.md](./ARCHITECTURE.md) for how it works.

**Q: How often is PROJECT_STATUS.md updated?**
A: It includes a CI run link. Check that link to see if the status is current.

**Q: Can I modify archived documents?**
A: Archived documents are read-only for reference. If you need to change something, move it back to the main docs directory and update it there.

**Q: Where do I report documentation issues?**
A: Create a GitHub issue titled `docs: [ISSUE]` and mention the specific document and line number.

**Q: How do I add a new document?**
A: Add it to the `docs/` root directory. Update this README with a new row in the Core Documentation table. Include version date and audience. Create a PR with the new document.

---

## Related Resources

- **Source code:** `backend/` (Python/FastAPI), `frontend/` (React/TypeScript)
- **Integration contract:** `~/AgentDev/shared/contracts/`
- **StockAgent project:** `~/AgentDev/StockAgent/docs/`
- **Platform guide:** `~/AgentDev/CLAUDE.md` (cross-project orchestration)

---

**Last Updated:** 2026-02-21
**Documentation Version:** 1.0
