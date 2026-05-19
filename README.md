# StudyPilot 🚀

**StudyPilot** is an AI-powered Telegram Mini App for personalized learning, focus sessions, knowledge management, and progress analytics.

It helps users turn a large learning goal into a clear roadmap, receive daily focus tasks, run Pomodoro-style study sessions, upload learning materials, and ask questions about them through a RAG assistant.

> StudyPilot is not just a timer and not just an AI chat.  
> It is a personal learning operating system:  
> **goal → plan → focus → knowledge → analytics → roadmap adaptation**

---

## ✨ Product Idea

Self-learning usually fails not because people lack materials.

It fails because:

- it is hard to know where to start;
- big goals are difficult to break into stages;
- focus is easy to lose;
- progress is hard to measure;
- learning plans quickly stop matching real life.

**StudyPilot** solves this by creating a complete learning loop:

```txt
Goal
  ↓
Roadmap
  ↓
Daily tasks
  ↓
Focus sessions
  ↓
Knowledge base
  ↓
Analytics
  ↓
Weekly review
  ↓
Updated roadmap
```

---

## Production Readiness

Deployment notes live in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Monitoring and post-deploy checks live in [docs/MONITORING.md](docs/MONITORING.md).

Core release checks:

```sh
cd backend
pytest
uvicorn app.main:app --reload
```

```sh
cd frontend
npx playwright install chromium
npm run typecheck
npm run test
npm run build
npm run test:e2e
```

```sh
docker compose -f docker-compose.prod.yml --env-file .env.production up --build
docker compose -f docker-compose.prod.yml down
```

The Playwright e2e suite requires a local backend in test mode, a migrated test PostgreSQL database with pgvector, and fake AI providers. It must not use real OpenAI, Tensorix, or Telegram calls.

Backend health endpoints:

- `GET /health`
- `GET /health/ready`

Production must run with `APP_ENV=production`, `TESTING=false`, restricted `ALLOWED_ORIGINS`, valid Telegram Mini App settings, and real provider keys.
