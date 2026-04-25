# Learning OS Work Log

Last updated: 2026-04-23

## Repository Context

- Project root contains `backend`, `frontend`, `bot`, `nginx`, `deploy`.
- `.env` is ignored by git at repo root.

## Completed Work

### 1) Backend FastAPI Scaffold

- Implemented settings, async DB session factory, app bootstrap, CORS, lifespan logs, and `/health`.
- Added API routers for users, plans, focus, ask, and analytics with placeholders.
- Added `backend/tests` scaffold with `conftest.py`, `test_health.py`, and `test_auth.py`.
- Added test and lint dependencies in `backend/requirements.txt`.

### 2) Telegram WebApp Auth (Backend)

- Implemented Telegram `initData` signature validation in `backend/app/middlewares/auth.py` using stdlib `hmac` and `hashlib`.
- Replaced the `get_current_user` dependency with real `Authorization: tma <initData>` validation.
- Implemented `/api/v1/users/me` to return Telegram user data from validated `initData`.

### 3) Frontend Telegram Integration

- Added Telegram SDK helpers in `frontend/src/lib/telegram.ts`.
- Added an axios API client with an `Authorization: tma ...` interceptor in `frontend/src/lib/api.ts`.
- Added the `useCurrentUser` hook and main app rendering state in `frontend/src/main.tsx`.
- Added minimal Vite app bootstrap files in `frontend/package.json`, `frontend/index.html`, `frontend/tsconfig.json`, and `frontend/vite.config.ts`.
- Added `frontend/.env` with `VITE_API_BASE_URL=http://localhost:8000`.

### 4) Bot Scaffold And Runtime

- Implemented the aiogram 3 bot scaffold with config, start handler, notification stubs, middleware, and polling/webhook entrypoint.
- Added the `/start` WebApp button, `Open Learning OS`, and logging.
- Confirmed that bot polling starts successfully and the token is valid with a passing `getMe` check.

### 5) DevOps And Deployment Scaffold

- Added nginx reverse proxy config and nginx Dockerfile.
- Added deploy scripts in `deploy/setup.sh` and `deploy/deploy.sh`, plus the systemd unit `deploy/learningos-api.service`.
- Added `docker-compose.yml` with local `postgres` and `redis` services.

### 6) Local Sprint 1 Validation

- `docker compose up -d` passed with `postgres` and `redis` running.
- Backend run passed: `/docs` is reachable and `/health` returns `{ "status": "ok", "version": "0.1.0" }`.
- Backend tests passed: `4 passed`.
- Bot polling run passed, `/start` was processed, and the WebApp button was shown.
- Confirmed Telegram contact and Mini App open flow from the bot message.
- For HTTPS Mini App testing, installed tunnel tooling:
- `ngrok` installation succeeded but requires an account authtoken.
- `cloudflared` quick tunnel was used as a fallback.
- Added a tunnel host allowlist in `frontend/vite.config.ts` and the matching CORS origin in `backend/.env`.

### 7) Frontend WebApp Bootstrap Verification (2026-04-14)

What was done:
- Initialized Vite, React, and TypeScript.
- Installed and configured `@twa-dev/sdk`.
- Added `src/lib/telegram.ts` with WebApp SDK utilities.
- Added `src/lib/api.ts` with an axios client using `tma` authorization.
- Connected the Telegram script in `index.html`.
- `npm run build` passed.
- `npx tsc --noEmit` passed.
- The dev server responds on `:5173`.

## [Sprint 2] Design System
Date: 2026-04-15
Status: completed

What was done:
- `src/styles/theme.css` with CSS variables from Telegram theme params
- `src/styles/global.css` with a base reset
- `src/hooks/useTelegramTheme.ts` for live theme updates
- `src/components/ui/` with Button, Card, Badge, Typography, and Divider
- `src/pages/DevKit.tsx` as a component showcase
- `npx tsc --noEmit` passed
- `npm run build` passed
- Dev server on `:5173` passed

Telegram test order:
1. Verify the frontend build with `npx tsc --noEmit` and `npm run build`.
2. Start the backend with `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
3. Verify the backend with `GET /health` returning `{"status":"ok","version":"0.1.0"}`.
4. Start the frontend with `npm run dev` on port `5173`.
5. Verify the frontend with `curl http://localhost:5173` returning HTTP `200`.
6. Start `cloudflared` HTTPS tunnels for `:8000` and `:5173`.
7. Point the bot WebApp URL to the frontend tunnel and verify that the Mini App opens from `/start`.
8. Verify in Telegram that the DevKit screen loads and theme params apply in both light and dark mode.
9. Finish the test by stopping `uvicorn`, `vite`, `cloudflared`, and `bot`.

## [Sprint 2] Navigation And Screens
Date: 2026-04-15
Status: completed

What was done:
- `src/router.tsx` with `react-router-dom` and 4 routes
- `src/components/layout/` with Layout, BottomNav, and BottomTab
- `src/components/ui/Skeleton.tsx` with shimmer animation
- `src/pages/` with TodayPage, RoadmapPage, KnowledgePage, and AnalyticsPage
- Bottom tabs with SVG icons and active state
- `safe-area-inset-bottom` support for iPhone
- `npx tsc --noEmit` passed
- `npm run build` passed

## [Sprint 2] API Client And Hooks
Date: 2026-04-16
Status: completed

What was done:
- `src/types/api.ts` with all entity types
- `src/lib/api.ts` with the axios instance, interceptors, and `apiClient` methods
- `src/hooks/useApi.ts` as a reusable hook with `AbortController`
- `src/hooks/useCurrentUser.ts`, `usePlan.ts`, `useFocus.ts`, and `useAnalytics.ts`
- Hooks connected to four screens for either data or skeleton states
- `npx tsc --noEmit` passed
- `npm run build` passed

## [Sprint 3] Roadmap Agent
Date: 2026-04-17
Status: completed

What was done:
- `app/agents/llm_client.py` with a Tensorix AsyncOpenAI client using `deepseek/deepseek-chat-v3.1`
- `app/agents/prompts/roadmap.py` with system and user prompts
- `app/agents/roadmap.py` with `RoadmapAgent` and JSON validation
- `POST /api/v1/plans` connected to the agent
- `tests/test_roadmap_agent.py` as an integration test with a real LLM
- Test passed and the LLM returns a valid plan

## [Sprint 3] Daily Coach Agent
Date: 2026-04-19
Status: completed

What was done:
- `app/agents/prompts/daily_coach.py` with system and user prompts
- `app/schemas/focus_block.py` with `FocusBlock` and `DailyPlan` on Pydantic v2
- `app/agents/daily_coach.py` with `DailyCoachAgent` validated through Pydantic
- `GET /api/v1/plans/current/today` connected to the agent
- `tests/test_daily_coach.py` with 4 unit tests using a mocked LLM
- `tests/test_daily_coach_integration.py` as an integration test

## [Спринт 3] Экран "Сегодня"
Дата: 2026-04-20
Статус: ✅ завершено

Что сделано:
- `src/hooks/useTodayPlan.ts` — параллельные запросы + sessionStorage прогресс
- `src/components/today/StageProgress.tsx` — прогресс-бар этапа (4 теста ✅)
- `src/components/today/FocusBlockCard.tsx` — карточка блока, 4 состояния (5 тестов ✅)
- `src/components/today/DailyNote.tsx` — заметка дня
- `src/pages/TodayPage.tsx` — полный экран, 4 состояния
- `npx tsc --noEmit` — OK
- `npm run build` — OK
- `npm run test` — все тесты зелёные ✅

## [Спринт 3] Связка Roadmap ↔ Daily Coach
Дата: 2026-04-20
Статус: ✅ завершено

Что сделано:
- `backend/app/api/plans.py` — `POST /plans` сохраняет roadmap в runtime-хранилище
- `backend/app/api/plans.py` — `GET /plans/current` возвращает текущий сохранённый план
- `backend/app/api/plans.py` — `GET /plans/current/today` генерирует Daily Coach из реального текущего этапа
- `backend/app/api/focus.py` — реализованы `POST /focus/start`, `POST /focus/end`, `GET /focus/history`
- `backend/app/repositories/runtime_store.py` — добавлено user-scoped in-memory состояние: plan/stages/focus history
- `backend/app/schemas/focus_session.py` — добавлена схема `FocusSession`
- `backend/tests/test_plan_persistence.py` — добавлены тесты на сохранение roadmap и использование истории focus в today-plan
- `pytest tests/test_plan_persistence.py tests/test_daily_coach.py -v` — 6 passed ✅

Текущий лимит реализации:
- Сохранение roadmap/focus реализовано в памяти процесса (runtime store).
- После рестарта backend состояние сбрасывается; постоянное хранение в PostgreSQL остаётся следующим шагом.

## [Sprint 3] Plan API
Date: 2026-04-21
Status: completed

What was done:
- `app/models/plan.py` with ORM `Plan` and `PlanStage` plus relationship mapping
- `app/repositories/plan_repository.py` with create/get/update helpers and current-stage lookup
- `app/schemas/plan.py` with `PlanRead`, `PlanStageRead`, and `PlanStageStatusUpdate`
- `app/api/plans.py` with 6 DB-backed endpoints wired to the roadmap and daily coach agents
- `tests/test_plan_repository.py` with 4 unit tests using a mocked DB
- Verified app startup and OpenAPI exposure for `plans`

Checks:
- ORM import check passed
- Repository import check passed
- Plan schema import check passed
- `GET /health` returned `{"status":"ok","version":"0.1.0"}`
- `pytest tests/test_plan_repository.py -v` passed with `4 passed`
- OpenAPI contains `/api/v1/plans`

## [Спринт 4] Focus Agent
Дата: 2026-04-23
Статус: ✅ завершено

Что сделано:
- `app/models/focus_log.py` — ORM FocusLog
- `app/schemas/focus_log.py` — FocusSessionStart, FocusSessionEnd, FocusSessionRead
- `app/repositories/user_repository.py` — get_or_create_by_telegram_id
- `app/repositories/focus_repository.py` — start, end, active, history, today
- `app/agents/focus.py` — FocusAgent: сообщения, логика перерывов, reminder
- `app/api/focus.py` — 4 эндпоинта: start, end, active, history
- `app/api/focus.py` — `user_id` резолвится через UserRepository, не через `UUID(int=telegram_id)`
- `tests/test_focus_agent.py` — 5 unit-тестов ✅
- `tests/test_focus_repository.py` — 3 unit-теста ✅
- `8` тестов — все зелёные ✅

Известные ограничения:
- Пауза не реализована (out of scope спринта 4)
- Уведомления бота — TODO, подключить после интеграции бота с бэком

## [Спринт 4] Pomodoro-таймер
Дата: 2026-04-25
Статус: ✅ завершено

Что сделано:
- `src/hooks/usePomodoro.ts` — polling 5s + локальный тик каждую секунду
- `src/lib/api.ts` — добавлен `apiClient.getActiveSession`
- `src/components/timer/CircularTimer.tsx` — SVG таймер (4 теста ✅)
- `src/components/timer/DifficultyPicker.tsx` — bottom sheet оценки (3 теста ✅)
- `src/components/timer/StartForm.tsx` — форма темы (3 теста ✅)
- `src/components/timer/PomodoroScreen.tsx` — оркестратор состояний
- `src/pages/TodayPage.tsx` — интеграция, fullscreen оверлей при активной сессии
- `npx tsc --noEmit` — OK
- `npm run build` — OK
- `npm run test` — 10 новых тестов, общий прогон 27 тестов, все зелёные ✅

Архитектурное решение:
  Polling вместо WebSocket — проще деплой, достаточно для Pomodoro UX.
  Таймер считается на фронте по `started_at` из БД.

## Backlog (Alpha)
Date: 2026-04-18
Status: in progress

- The alpha version of the Roadmap mini app is locked in as the current stage.
- Issue: roadmap generation becomes unstable when the deadline is too close.

## Current Follow-ups

- Replace placeholder API endpoints in ask, analytics, and user update/delete with real logic.
- Replace the temporary tunnel URL with a permanent HTTPS domain for stable Mini App testing.
- Keep backend, bot, and frontend `.env` values aligned for production.
- Add a CI pipeline for tests and lint, plus a formal release workflow.

## Notes

- On Windows, `bot` pinned dependencies install reliably with Python 3.12.
- Root and service-level Makefiles currently use Unix-style `.venv/bin/...` commands and need Windows-specific alternatives for direct `make` usage on PowerShell.
