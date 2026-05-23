# 🚀 StudyPilot — AI Learning OS

> AI-powered Telegram Mini App that turns learning goals into adaptive roadmaps,  
> daily focus sessions, searchable knowledge, analytics, and weekly roadmap reviews.  
> Built with FastAPI, React, PostgreSQL, pgvector, Telegram Bot API, and AI agents.

---

## Why this exists

Most learning tools solve only one slice of the problem.

Notion stores plans.  
Pomodoro apps track time.  
ChatGPT answers questions.  
LMS platforms host courses.  
Habit trackers count streaks.

But real learning is not a set of disconnected tools.

Real learning is a loop:

```txt
Goal
  ↓
Plan
  ↓
Daily execution
  ↓
Focused work
  ↓
Knowledge retrieval
  ↓
Progress analytics
  ↓
Plan adaptation
```

I built **StudyPilot** because learners do not fail only because they lack information.

They fail because:

- the plan is unclear;
- the next action is vague;
- learning materials are scattered;
- focus is inconsistent;
- progress is invisible;
- AI tools answer without personal context;
- the roadmap does not adapt when reality changes.

StudyPilot turns that chaos into a system.

It is not just a Pomodoro timer.  
It is not just a RAG chatbot.  
It is not just a roadmap generator.

It is an AI learning operating system where every feature feeds the next one.

---

## Product Loop

```txt
User defines a goal
    ↓
Roadmap Agent creates a structured plan
    ↓
Daily Coach generates today's focus blocks
    ↓
Focus Agent tracks real study sessions
    ↓
Knowledge Base indexes uploaded materials
    ↓
RAG Agent answers with sources
    ↓
Analytics Agent measures progress
    ↓
Weekly Review compares plan vs reality
    ↓
Roadmap is adapted safely
```

The product is designed around one principle:

> A learning plan should not be static.  
> It should evolve as the learner evolves.

---

## Architecture

| Layer | Implementation |
|---|---|
| **Frontend** | React 18 + Vite + TypeScript Telegram Mini App |
| **Backend** | FastAPI + Pydantic v2 + async SQLAlchemy |
| **Database** | PostgreSQL 16 with raw SQL migrations |
| **Vector Search** | pgvector-backed semantic retrieval |
| **AI Providers** | Tensorix / OpenAI-compatible LLMs + OpenAI embeddings |
| **Agents** | Roadmap, Daily Coach, Focus, RAG, Analytics, Weekly Review |
| **Bot** | aiogram 3 Telegram bot for launch, reminders, and weekly digests |
| **Auth** | Telegram Mini App signed `initData` validation |
| **Deployment** | Docker, production Compose, Caddy, Railway workflows |
| **Testing** | Pytest, Ruff, Vitest, Playwright, GitHub Actions |

---

## System Design

```txt
Telegram User
    ↓
Telegram Mini App
    ↓
React Frontend
    ↓
FastAPI API Layer
    ↓
Service / Repository Layer
    ↓
PostgreSQL + pgvector
    ↓
LLM + Embedding Providers
    ↓
Telegram Bot Notifications
```

StudyPilot keeps the user experience lightweight through Telegram while the backend handles the serious work:

- identity validation;
- roadmap persistence;
- focus session constraints;
- document ingestion;
- embedding generation;
- vector indexing;
- grounded RAG answers;
- analytics aggregation;
- weekly review generation;
- safe roadmap mutation;
- Telegram digest delivery.

---

## What it does

### 🧭 Roadmap Agent

The learner enters:

- goal;
- current level;
- deadline;
- weekly availability.

The Roadmap Agent generates a structured learning plan:

- stages;
- milestones;
- deliverables;
- estimated workload;
- progress status.

The key decision: roadmap output is not treated as disposable text.  
It is persisted as product data and powers the rest of the app.

---

### 📅 Daily Coach

The Daily Coach turns the roadmap into daily execution.

It uses:

- active plan;
- current stage;
- deadlines;
- focus history;
- unfinished work;
- available study rhythm.

Instead of asking:

> “What should I study today?”

the learner gets concrete focus blocks.

---

### 🍅 Focus Agent

The Focus Agent manages Pomodoro-style sessions and writes real behavioral data.

It supports:

- start session;
- end session;
- active session lookup;
- session history;
- planned duration;
- actual duration;
- topic;
- difficulty;
- Telegram reminders.

This makes focus sessions more than a timer.  
They become the raw signal for analytics and roadmap adaptation.

---

### 📚 Knowledge Base

The learner uploads materials:

- TXT;
- Markdown;
- PDF.

The backend runs a full ingestion pipeline:

```txt
Upload
  ↓
Validate file
  ↓
Extract text
  ↓
Chunk document
  ↓
Generate embeddings
  ↓
Store chunks
  ↓
Index vectors in pgvector
  ↓
Make the material searchable
```

Documents become queryable memory.

---

### 🧠 RAG Agent

The RAG Agent answers questions using the learner's own documents.

| Step | Purpose |
|---|---|
| **Query Rewrite** | Converts vague questions into better retrieval queries |
| **Embedding** | Converts the query into vector space |
| **Vector Search** | Finds relevant chunks in pgvector |
| **Rerank** | Improves result ordering with lexical + semantic scoring |
| **Answer Generation** | Produces a grounded response |
| **Sources** | Returns snippets and citations |

Design rule:

> If the answer is not in the user's materials, the agent says so.

No fake certainty.  
No hallucinated “probably”.  
No AI magic smoke.

---

### 📊 Analytics Agent

The Analytics Agent turns study activity into feedback.

It calculates:

- focus minutes;
- session count;
- cancelled sessions;
- completion rate;
- streak;
- best focus hours;
- topic progress;
- daily breakdown;
- weekly breakdown;
- AI-assisted recommendations.

Example metrics:

| Metric | Meaning |
|---|---|
| **Focus Time** | Completed study time |
| **Completion Rate** | Completed sessions vs cancelled sessions |
| **Streak** | Consecutive active study days |
| **Best Hours** | Time windows with strongest focus |
| **Topic Progress** | Where effort is actually going |

The point is not charts for decoration.

The point is feedback that changes behavior.

---

### 🔁 Weekly Review Agent

The Weekly Review Agent compares roadmap expectations with actual behavior.

It asks:

- What was planned this week?
- What actually happened?
- Which stages are behind?
- Which topics consumed more time than expected?
- Is the learner on track, behind, ahead, or lacking data?
- What should change next week?

It can propose:

- rescheduling a stage;
- splitting a large stage;
- marking a stage as risky;
- adjusting focus load.

Critical safety rule:

> The AI can propose.  
> The backend validates.  
> The user or safe service flow applies.

The model never directly mutates the roadmap.

---

### 📬 Telegram Weekly Digest

Every Sunday, the bot can send a weekly report:

```txt
📊 Weekly StudyPilot Report

Focus: 7h 00m
Sessions: 18
Completion rate: 85%
Streak: 5 days

Best hours: 09:00, 11:00, 19:00

Top topics:
• RAG — 2h 40m
• PostgreSQL — 1h 30m
• FastAPI — 45m
```

The digest uses:

- analytics metrics;
- optional weekly review data;
- duplicate delivery prevention;
- delivery status tracking;
- Telegram error handling.

---

## Engineering Decisions

**Telegram Mini App instead of a traditional web app.**  
Telegram gives identity, mobile-first UX, notifications, and zero-friction entry. The user does not need another account or another app.

**FastAPI for the backend.**  
The product needs typed APIs, async IO, OpenAPI docs, background-friendly service logic, and fast iteration.

**PostgreSQL as the source of truth.**  
Plans, stages, sessions, documents, chunks, reviews, notifications, and analytics need relational consistency.

**pgvector for MVP semantic search.**  
Keeping vectors inside PostgreSQL avoids extra infrastructure while preserving future migration flexibility through `VectorIndexService`.

**Thin routers. Real services.**  
Routers expose contracts. Services own behavior. Repositories own data access.

**AI output is untrusted input.**  
Roadmaps, review proposals, and structured AI output are validated before persistence or mutation.

**User isolation is non-negotiable.**  
Every document, chunk, focus session, plan, analytics query, and review is scoped by `user_id`.

**Fake providers for tests. Real providers for production.**  
No real OpenAI, Telegram, or external vector calls are required in tests.

---

## API Surface

### Health

```http
GET /health
GET /health/ready
```

### Users

```http
GET    /api/v1/users/me
PUT    /api/v1/users/me        # currently 501
DELETE /api/v1/users/me        # currently 501
```

### Plans

```http
POST  /api/v1/plans/
GET   /api/v1/plans/current
GET   /api/v1/plans/current/today
GET   /api/v1/plans/{plan_id}
POST  /api/v1/plans/{plan_id}/recalculate
PATCH /api/v1/plans/stages/{stage_id}
```

### Focus

```http
POST /api/v1/focus/start
POST /api/v1/focus/end
GET  /api/v1/focus/active
GET  /api/v1/focus/history
```

### Documents + RAG

```http
POST   /api/v1/documents/upload
GET    /api/v1/documents
GET    /api/v1/documents/{document_id}
DELETE /api/v1/documents/{document_id}
POST   /api/v1/ask
```

### Analytics

```http
GET /api/v1/analytics/daily
GET /api/v1/analytics/weekly
GET /api/v1/analytics/today
GET /api/v1/analytics/week
GET /api/v1/analytics/streak
```

### Weekly Review

```http
POST /api/v1/weekly-review/generate
POST /api/v1/weekly-review/{review_id}/apply
GET  /api/v1/weekly-review/history
```

---

## Data Model

| Table | Purpose |
|---|---|
| `users` | Telegram identity, timezone, preferences |
| `plans` | Learning goals and roadmap metadata |
| `plan_stages` | Roadmap stages, dates, statuses, workload |
| `focus_log` | Pomodoro and focus session history |
| `documents` | Uploaded materials and processing state |
| `document_chunks` | Text chunks, metadata, embeddings |
| `metrics` | Aggregated or derived learning metrics |
| `notification_jobs` | Telegram notification scheduling |
| `weekly_reviews` | AI-assisted plan-vs-reality reviews |
| `weekly_digest_deliveries` | Telegram digest delivery tracking |

---

## Repository Structure

```txt
learning-os/
├── backend/
│   ├── app/
│   │   ├── agents/          # LLM clients, roadmap/focus/daily-coach agents
│   │   ├── api/             # FastAPI routers
│   │   ├── middlewares/     # auth and request logging
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # database access
│   │   ├── schemas/         # Pydantic contracts
│   │   ├── services/        # business logic, RAG, analytics, workers
│   │   └── main.py
│   ├── migrations/          # raw SQL migrations
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/             # API client and Telegram helpers
│   │   ├── pages/
│   │   ├── styles/
│   │   ├── types/
│   │   └── utils/
│   ├── e2e/                 # Playwright tests
│   └── package.json
│
├── bot/
│   ├── handlers/
│   ├── keyboards/
│   ├── middlewares/
│   └── main.py
│
├── deploy/                  # Caddy/systemd/deploy/migration helpers
├── docs/                    # deployment and monitoring notes
├── nginx/
├── scripts/
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

---

## Stack

`Python` · `FastAPI` · `Pydantic v2` · `SQLAlchemy` · `PostgreSQL` · `pgvector`  
`React` · `Vite` · `TypeScript` · `Telegram Mini Apps`  
`aiogram` · `LLM Agents` · `Embeddings` · `RAG` · `Docker` · `Playwright`

---

## Local Development

### 1. Create env files

```powershell
Copy-Item .env.example .env
Copy-Item .env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

For local frontend development:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

For local development without external noise:

```env
NOTIFICATIONS_ENABLED=false
WEEKLY_DIGEST_ENABLED=false
ANALYTICS_AI_ENABLED=false
WEEKLY_REVIEW_AI_ENABLED=false
```

### 2. Start PostgreSQL

```powershell
docker compose up -d postgres redis
```

Run migrations:

```powershell
Get-ChildItem backend\migrations\*.sql | Sort-Object Name | ForEach-Object {
  Get-Content $_.FullName | docker exec -i learning-os-postgres psql -U postgres -d learning_os -v ON_ERROR_STOP=1
}
```

### 3. Run backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health/ready
```

### 4. Run frontend

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```txt
http://127.0.0.1:5173
```

### 5. Run bot

```powershell
cd bot
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Required bot env:

```env
BOT_TOKEN=your_telegram_bot_token
MINI_APP_URL=https://your-mini-app-url.example
USE_WEBHOOK=false
```

---

## Testing

### Backend

```powershell
cd backend
$env:APP_ENV = "test"
$env:TESTING = "true"
$env:LLM_PROVIDER = "fake"
$env:EMBEDDING_PROVIDER = "fake"
$env:NOTIFICATIONS_ENABLED = "false"
$env:WEEKLY_DIGEST_ENABLED = "false"
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m ruff format --check app
.\.venv\Scripts\python.exe -m pytest tests -q
```

### Frontend

```powershell
cd frontend
npm run typecheck
npm run test
npm run build
```

### E2E

```powershell
cd frontend
npm run test:e2e
```

Local Playwright execution requires:

- running test backend;
- migrated pgvector database;
- installed Chromium.

The GitHub `E2E Checks` workflow runs this path with fake AI providers.

---

## Production Deployment

Production safety checks enforce:

- `APP_ENV=production`;
- `TESTING=false`;
- `TEST_AUTH_ENABLED=false`;
- strong `SECRET_KEY`;
- real Telegram bot token;
- HTTPS `MINI_APP_URL`;
- restricted HTTPS `ALLOWED_ORIGINS`;
- provider keys for selected LLM/embedding providers;
- non-empty `INTERNAL_JOBS_SECRET`;
- no fake providers outside test mode.

Run production stack:

```powershell
Copy-Item .env.production.example .env.production
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

The production Compose stack includes:

- `postgres` with `pgvector/pgvector:pg16`;
- one-shot migration service;
- FastAPI backend;
- static frontend served through nginx;
- polling-mode Telegram bot;
- Caddy reverse proxy with automatic HTTPS.

More detail:

- [Deployment guide](docs/DEPLOYMENT.md)
- [Monitoring guide](docs/MONITORING.md)

---

## CI/CD

Pull request checks run:

- frontend install, typecheck, tests, and build;
- backend migrations against pgvector Postgres;
- Ruff checks;
- Pytest;
- bot import check.

Main-branch e2e checks run Playwright against a seeded test backend with fake AI providers.

Railway workflows exist for:

- backend;
- frontend;
- bot.

---

## Environment

```env
APP_ENV=development
TESTING=false
APP_VERSION=0.1.0
LOG_LEVEL=INFO

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/learning_os
SECRET_KEY=dev-secret-key-change-me
MINI_APP_URL=http://localhost:5173
ALLOWED_ORIGINS=["http://localhost:5173"]
INTERNAL_JOBS_SECRET=dev-internal-jobs-secret

BOT_TOKEN=123456:TEST_TOKEN
TELEGRAM_BOT_TOKEN=123456:TEST_TOKEN

LLM_PROVIDER=tensorix
TENSORIX_API_KEY=
TENSORIX_BASE_URL=https://api.tensorix.ai/v1
TENSORIX_MODEL=deepseek/deepseek-chat-v3.1

EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

VECTOR_STORE_PROVIDER=pgvector

NOTIFICATIONS_ENABLED=false
WEEKLY_DIGEST_ENABLED=false
ANALYTICS_AI_ENABLED=false
WEEKLY_REVIEW_AI_ENABLED=false
```

See `.env.example` and `.env.production.example` for the full list.

---

## Security Principles

- Telegram `initData` is the auth boundary.
- Test auth is blocked outside test mode.
- Every critical query is scoped by `user_id`.
- RAG search never crosses user boundaries.
- Uploaded files are validated by size and type.
- Internal endpoints require secrets.
- AI output is validated before persistence or mutation.
- Secrets are not logged.
- Full document contents are not dumped into logs.
- Fake providers are test-only.

---

## Current Status

Production-MVP readiness is implemented.

Completed:

- Telegram Mini App auth through signed `initData`;
- roadmap generation and persisted plan/stage data;
- Daily Coach generation from current roadmap;
- Pomodoro/focus session tracking with active-session protection;
- Knowledge Base uploads for TXT, Markdown, and PDF;
- document chunking, embeddings, pgvector indexing, and user-scoped RAG;
- analytics metrics, charts, and AI-assisted reports;
- Weekly Review backend flow with validated roadmap change proposals;
- weekly Telegram digest worker and delivery tracking;
- health/readiness endpoints;
- request logging;
- production config validation;
- Docker production stack;
- CI;
- Playwright e2e scaffolding.

---

## Known Follow-ups

- Dedicated Mini App UI for Weekly Review.
- `PUT /api/v1/users/me` and `DELETE /api/v1/users/me` currently return `501`.
- Stable production Telegram testing requires a permanent HTTPS domain and BotFather Mini App URL configuration.
- Local e2e runs need Chromium plus a migrated pgvector test database.
- Root/service Makefiles currently assume Unix-style virtualenv paths; PowerShell commands are safer on Windows.

---

## Results

StudyPilot demonstrates:

- full-stack product engineering;
- Telegram platform integration;
- production-minded FastAPI architecture;
- PostgreSQL data modeling and migrations;
- personal RAG over uploaded documents;
- AI agent orchestration around real product state;
- analytics and review workflows;
- safe AI-generated roadmap adaptation;
- Docker, CI, health checks, readiness checks, and e2e scaffolding.

This is not a notebook demo.  
This is not an API wrapper.

It is a full-stack AI product where every component supports the same learning loop.

---

## What I learned building it

The hard part was not calling an LLM.

The hard part was making AI behave like a reliable product feature:

- structured outputs;
- validation;
- user isolation;
- fallbacks;
- deterministic metrics;
- safe mutations;
- test providers;
- production config;
- real user flows.

StudyPilot connects product thinking, backend architecture, AI agents, RAG, analytics, and deployment into one system.

---

## For recruiters

This project demonstrates practical experience with:

- full-stack architecture;
- AI product engineering;
- RAG systems;
- vector search;
- production API design;
- Telegram Mini App integration;
- data modeling;
- async backend services;
- frontend product flows;
- testing strategy;
- deployment readiness;
- user-centered engineering.

StudyPilot was built to show that I can do more than ship isolated endpoints.

I can design and build the system around them.

---

<div align="center">
  <sub>Built to turn learning from chaos into a system.</sub>
</div>
