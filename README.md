# 🚀 StudyPilot — AI Learning Operating System

> Telegram Mini App that turns goals into roadmaps, roadmaps into focus sessions,  
> study materials into a searchable knowledge base, and raw effort into measurable progress.  
> Built with **React**, **FastAPI**, **PostgreSQL**, **pgvector**, **Telegram Bot API**, and **AI agents**.

---

## Why this exists

Most learning apps help you **store information**.  
Most AI tools help you **ask questions**.  
Most productivity tools help you **track time**.

But real learning breaks somewhere between all three.

People start with a goal:

> “I want to become backend-ready.”  
> “I need to prepare for an internship.”  
> “I have 8 weeks to learn FastAPI, PostgreSQL, Docker, and RAG.”

Then reality hits:

- the plan becomes outdated;
- focus disappears;
- notes get scattered;
- materials are hard to search;
- progress is invisible;
- AI answers without personal context;
- motivation dies quietly somewhere around week two.

**StudyPilot** exists to solve that.

It is not a Pomodoro timer.  
It is not a Notion clone.  
It is not a random AI wrapper.

It is a learning system that connects:

```txt
Goal
  ↓
AI-generated roadmap
  ↓
Daily focus plan
  ↓
Pomodoro sessions
  ↓
Knowledge base with RAG
  ↓
Analytics
  ↓
Weekly review
  ↓
Adapted roadmap
```

The goal is simple:

> Help people study like a system, not like chaos.

---

## What it does

StudyPilot is a Telegram Mini App where a learner can:

- define a learning goal;
- generate a personalized roadmap;
- receive daily study blocks;
- run focus sessions;
- upload documents;
- ask questions over personal materials;
- track progress;
- receive weekly AI reviews;
- adapt the roadmap based on actual performance.

---

## Core Product Loop

```txt
User sets a goal
    ↓
Roadmap Agent creates a plan
    ↓
Daily Coach selects today's focus blocks
    ↓
Focus Agent tracks Pomodoro sessions
    ↓
Knowledge Base stores learning materials
    ↓
RAG Agent answers questions with sources
    ↓
Analytics Agent measures progress
    ↓
Weekly Review Agent compares plan vs reality
    ↓
Roadmap gets adjusted safely
```

StudyPilot is designed around one idea:

> A plan should not be static. It should evolve as the learner evolves.

---

## Architecture

| Layer | Implementation |
|---|---|
| **Frontend** | Telegram Mini App built with React, Vite, and TypeScript |
| **Backend** | FastAPI service with typed routers, schemas, services, and repositories |
| **Database** | PostgreSQL for users, plans, focus logs, documents, analytics, and reviews |
| **Vector Search** | pgvector for embeddings and semantic document retrieval |
| **AI Agents** | Roadmap, Daily Coach, Focus, RAG, Analytics, and Weekly Review agents |
| **Bot Layer** | Telegram Bot API for app entry, focus reminders, and weekly digests |
| **Auth** | Telegram Mini App `initData` validation, no passwords required |
| **Deployment** | Docker-ready architecture with health checks and production config |
| **Testing** | Backend tests, frontend checks, and planned e2e critical flows |

---

## System Design

```txt
Telegram User
    ↓
Telegram Mini App
    ↓
React Frontend
    ↓
FastAPI Backend
    ↓
PostgreSQL + pgvector
    ↓
AI Services / LLM / Embeddings
    ↓
Telegram Bot Notifications
```

StudyPilot keeps the user experience lightweight through Telegram, while the backend handles the heavy lifting:

- roadmap generation;
- document ingestion;
- vector indexing;
- RAG answering;
- analytics aggregation;
- weekly review logic;
- notification delivery.

---

## Main Features

### 🧭 Roadmap Agent

The user provides:

- learning goal;
- current level;
- deadline;
- available weekly hours.

The Roadmap Agent creates a structured learning plan with:

- stages;
- weekly milestones;
- deliverables;
- estimated workload;
- progress tracking.

The roadmap is not just text.  
It becomes structured data that the rest of the system can use.

---

### 📅 Daily Coach Agent

The Daily Coach converts the roadmap into daily execution.

It generates practical focus blocks based on:

- current roadmap stage;
- deadline pressure;
- user availability;
- previous progress;
- unfinished tasks;
- focus history.

The goal is to remove the daily question:

> “What should I study today?”

StudyPilot answers that automatically.

---

### 🍅 Focus Agent

The Focus Agent manages Pomodoro-style study sessions.

It supports:

- starting a session;
- ending a session;
- storing history;
- tracking planned duration;
- calculating actual duration;
- recording topic;
- recording difficulty;
- detecting active sessions;
- sending Telegram reminders.

Focus sessions are stored as real analytics data, not just timer state.

---

### 📚 Knowledge Base

Users can upload learning materials:

- PDF;
- TXT;
- Markdown;
- potentially DOCX.

The backend processes every document through an ingestion pipeline:

```txt
Upload file
  ↓
Validate file
  ↓
Extract text
  ↓
Split into chunks
  ↓
Generate embeddings
  ↓
Store chunks
  ↓
Index vectors
  ↓
Make document searchable
```

The Knowledge Base turns static files into an interactive learning memory.

---

### 🧠 RAG Agent

The RAG Agent answers questions using the user's own documents.

| Step | Description |
|---|---|
| **Query Rewrite** | Turns vague questions into better semantic search queries |
| **Embedding** | Converts the rewritten query into a vector |
| **Vector Search** | Retrieves relevant chunks from pgvector |
| **Rerank** | Reorders chunks by semantic and lexical relevance |
| **Answer Generation** | Produces a grounded answer |
| **Sources** | Returns document snippets and citations |

The agent follows one strict rule:

> If the answer is not in the user's materials, say that clearly.

No fake confidence.  
No random hallucinated facts.  
No “trust me bro” AI behavior.

---

### 📊 Analytics Agent

The Analytics Agent transforms raw activity into insight.

It calculates:

- total focus time;
- session count;
- cancelled sessions;
- completion rate;
- average session duration;
- streak;
- best focus hours;
- most focused topics;
- daily and weekly breakdowns.

| Metric | Meaning |
|---|---|
| **Focus Time** | Total completed study time |
| **Completion Rate** | Completed sessions vs cancelled sessions |
| **Streak** | Consecutive days with completed focus |
| **Best Hours** | Time windows where the user performs best |
| **Topic Progress** | Where the user spends most effort |

The point is not just charts.

The point is self-awareness.

---

### 🔁 Weekly Review Agent

The Weekly Review Agent compares the plan with reality.

It asks:

- What was planned?
- What was actually completed?
- Which stages are behind?
- Which topics consumed more time?
- Was the user consistent?
- Should the roadmap change?

It can propose safe changes:

- reschedule a stage;
- split a large stage;
- mark a stage as risky;
- adjust recommended focus load.

Important design choice:

> The AI never directly rewrites the roadmap without validation.

Proposed changes are stored, reviewed, and applied safely.

---

## Engineering Decisions

**Telegram Mini App over a traditional web app.**  
The user does not need another account, another app, or another dashboard. Telegram gives instant access, identity, notifications, and mobile-first UX.

**FastAPI for backend.**  
The app needs clean APIs, async support, strong typing, OpenAPI docs, and fast iteration.

**PostgreSQL as the source of truth.**  
Plans, stages, focus logs, documents, chunks, reviews, and analytics need relational integrity, transactions, indexes, JSONB, and migrations.

**pgvector over a separate vector database for MVP.**  
Since the app already uses PostgreSQL, pgvector keeps deployment simple while still supporting semantic search. Future migration to Qdrant remains possible through `VectorIndexService`.

**Thin routers, strong service layer.**  
Business logic lives in services: `RoadmapAgent`, `FocusService`, `DocumentIngestService`, `VectorIndexService`, `RAGAgent`, `AnalyticsMetricsService`, and `WeeklyReviewService`.

**User isolation everywhere.**  
Every critical query is scoped by `user_id`: documents, chunks, RAG, focus history, analytics, plans, and weekly reviews.

**AI output is treated as untrusted input.**  
The model can suggest. The backend verifies. That is the difference between a fun demo and an actual product.

---

## API Surface

### Focus API

```http
POST /focus/start
POST /focus/end
GET  /focus/history
```

### Documents API

```http
POST   /documents/upload
GET    /documents
GET    /documents/{document_id}
DELETE /documents/{document_id}
```

### RAG API

```http
POST /ask
```

### Analytics API

```http
GET /analytics/daily
GET /analytics/weekly
```

### Weekly Review API

```http
POST /weekly-review/generate
POST /weekly-review/{review_id}/apply
GET  /weekly-review/history
```

---

## Data Model Overview

| Table | Purpose |
|---|---|
| `users` | Telegram users and preferences |
| `plans` | Learning goals and roadmap metadata |
| `plan_stages` | Roadmap stages, deadlines, statuses |
| `focus_log` | Focus sessions and Pomodoro history |
| `documents` | Uploaded materials and processing status |
| `document_chunks` | Chunked text, metadata, and embeddings |
| `weekly_reviews` | AI-generated plan-vs-reality reviews |
| `weekly_digest_deliveries` | Telegram weekly digest delivery status |
| `metrics` | Aggregated or derived learning metrics |

---

## RAG Pipeline

```txt
Question
  ↓
Query rewrite
  ↓
Question embedding
  ↓
pgvector similarity search
  ↓
User/document filters
  ↓
Reranking
  ↓
Context assembly
  ↓
Grounded answer generation
  ↓
Answer with sources
```

Source response example:

```json
{
  "answer": "The document recommends preparing your CV, GitHub, and project explanations before applying.",
  "sources": [
    {
      "document_title": "Ericsson Intern Preparation",
      "filename": "ericsson_intern_rag_test_document.md",
      "chunk_index": 4,
      "page_number": null,
      "snippet": "CV should be short, relevant, and adapted to the internship role..."
    }
  ],
  "confidence": "high"
}
```

---

## Analytics Logic

### Completion Rate

```txt
completed_sessions / (completed_sessions + cancelled_sessions) * 100
```

### Streak

A day counts toward streak if it has at least one completed focus session.

### Best Focus Hours

Completed sessions are grouped by local hour.  
The system returns the hours with the highest productive focus time.

### Topic Progress

Focus minutes are aggregated by session topic.

---

## Production Readiness

StudyPilot is designed with production-MVP concerns in mind:

- environment-based configuration;
- no hardcoded secrets;
- Docker-ready services;
- health and readiness endpoints;
- protected internal endpoints;
- Telegram API error handling;
- vector store cleanup on document deletion;
- no real external calls in tests;
- user-scoped data access;
- safe AI-generated changes;
- migration-based database evolution.

---

## Testing Strategy

| Area | What is tested |
|---|---|
| **Backend** | API contracts, services, auth, user isolation |
| **Focus** | Start/end session, active session constraints |
| **Documents** | Upload, validation, ingestion, deletion |
| **RAG** | Query rewrite fallback, vector search, sources |
| **Analytics** | Streak, completion rate, best hours, topics |
| **Weekly Review** | Plan-vs-fact analysis, safe apply logic |
| **Frontend** | Main screens, loading/error states, navigation |
| **E2E** | Critical user flows from goal to analytics |

Tests avoid real calls to:

- OpenAI;
- Telegram Bot API;
- external vector services.

---

## Project Structure

```txt
study-pilot/
├── frontend/
│   ├── src/
│   │   ├── api/               # API client and typed contracts
│   │   ├── components/        # Shared UI components
│   │   ├── screens/           # Today, Roadmap, Focus, Knowledge, Analytics
│   │   ├── hooks/             # Data fetching and app logic
│   │   └── utils/             # Formatting, dates, helpers
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI routers
│   │   ├── models/            # SQLAlchemy/SQLModel models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic and AI agents
│   │   ├── repositories/      # Database access
│   │   ├── core/              # Settings, auth, security
│   │   └── main.py
│   └── tests/
│
├── bot/
│   └── main.py                # Telegram bot entrypoint
│
├── migrations/                # Alembic migrations
├── docs/
│   ├── DEPLOYMENT.md
│   └── MONITORING.md
├── docker-compose.yml
└── README.md
```

---

## Stack

`Python` · `FastAPI` · `PostgreSQL` · `pgvector` · `SQLAlchemy` · `Alembic`  
`React` · `Vite` · `TypeScript` · `Telegram Mini Apps`  
`Telegram Bot API` · `LLM Agents` · `Embeddings` · `RAG` · `Docker`

---

## Run it locally

```bash
git clone https://github.com/your-username/study-pilot.git
cd study-pilot
docker compose up -d
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Bot

```bash
cd bot
python main.py
```

---

## Environment

```env
APP_ENV=development
APP_NAME=StudyPilot

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/studypilot
BACKEND_CORS_ORIGINS=http://localhost:5173

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_BOT_USERNAME=your_bot_username
MINI_APP_URL=https://your-mini-app-url.com

OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
RAG_REWRITE_MODEL=gpt-4o-mini
RAG_ANSWER_MODEL=gpt-4o-mini

VECTOR_STORE_PROVIDER=pgvector

NOTIFICATIONS_ENABLED=true
WEEKLY_DIGEST_ENABLED=true

INTERNAL_JOBS_SECRET=change_me
```

---

## Roadmap

### ✅ Sprint 1 — Infrastructure

- monorepo;
- PostgreSQL;
- FastAPI scaffold;
- Telegram Bot;
- Telegram Mini App auth.

### ✅ Sprint 2 — Mini App UI

- React + Vite;
- design system;
- navigation;
- API client;
- CI/CD.

### ✅ Sprint 3 — Roadmap + Daily Coach

- Roadmap Agent;
- Goal to Roadmap screen;
- Daily Coach Agent;
- Today screen;
- Plan API.

### ✅ Sprint 4 — Pomodoro + Focus

- Focus Agent;
- Pomodoro timer;
- Focus API;
- Telegram notifications;
- session history screen.

### ✅ Sprint 5 — RAG + Knowledge Navigator

- document ingest pipeline;
- RAG Agent;
- RAG API;
- Knowledge Base screen;
- pgvector integration.

### ✅ Sprint 6 — Analytics + Weekly Review

- Analytics Agent;
- Analytics screen;
- Weekly Review Agent;
- Telegram weekly digest;
- e2e tests and production polish.

---

## Results

StudyPilot demonstrates a complete AI product architecture:

- AI agents that operate on structured product data;
- personal RAG over uploaded documents;
- Telegram-native learning workflow;
- focus tracking connected to analytics;
- plan adaptation based on real behavior;
- production-oriented backend design;
- user isolation and safe AI validation.

This is not a notebook demo.

It is a full-stack AI application where every component supports the core learning loop.

---

## What I learned building it

Building StudyPilot required connecting multiple difficult areas:

- Telegram Mini App authentication;
- mobile-first frontend architecture;
- FastAPI service design;
- PostgreSQL relational modeling;
- pgvector semantic search;
- document ingestion;
- RAG answer grounding;
- AI agent orchestration;
- analytics aggregation;
- safe AI-generated roadmap updates;
- Telegram bot notifications;
- production readiness.

The hardest part was not calling an LLM.

The hardest part was turning AI into a reliable product feature.

---

## For recruiters

This project shows practical experience with:

- full-stack product engineering;
- backend architecture;
- AI agent design;
- RAG systems;
- vector databases;
- production API design;
- Telegram platform integration;
- data modeling;
- testing strategy;
- user-centered product thinking.

StudyPilot is built to show that I can ship more than isolated features.

I can design and build an entire system.

---

<div align="center">
  <sub>Built to turn learning from chaos into a system.</sub>
</div>
