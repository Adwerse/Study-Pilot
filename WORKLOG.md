# Learning OS Work Log

Last updated: 2026-04-15

## Repository Context

- Project root contains `backend`, `frontend`, `bot`, `nginx`, `deploy`.
- `.env` is ignored by git at repo root.

## Completed Work

### 1) Backend FastAPI Scaffold

- Implemented settings, async DB session factory, app bootstrap, CORS, lifespan logs, and `/health`.
- Added API routers for users/plans/focus/ask/analytics with placeholders.
- Added `backend/tests` scaffold (`conftest.py`, `test_health.py`, `test_auth.py`).
- Added test/lint dependencies in `backend/requirements.txt`.

### 2) Telegram WebApp Auth (Backend)

- Implemented Telegram `initData` signature validation in `backend/app/middlewares/auth.py` using stdlib `hmac` + `hashlib`.
- Replaced `get_current_user` dependency with real `Authorization: tma <initData>` validation.
- Implemented `/api/v1/users/me` to return Telegram user data from validated `initData`.

### 3) Frontend Telegram Integration

- Added Telegram SDK helpers (`frontend/src/lib/telegram.ts`).
- Added axios API client with `Authorization: tma ...` interceptor (`frontend/src/lib/api.ts`).
- Added `useCurrentUser` hook and main app rendering state in `frontend/src/main.tsx`.
- Added minimal Vite app bootstrap files (`frontend/package.json`, `frontend/index.html`, `frontend/tsconfig.json`, `frontend/vite.config.ts`).
- Added `frontend/.env` with `VITE_API_BASE_URL=http://localhost:8000`.

### 4) Bot Scaffold and Runtime

- Implemented aiogram 3 bot scaffold (config, start handler, notifications stubs, middleware, polling/webhook entrypoint).
- Added `/start` WebApp button (`Open Learning OS`) and logging.
- Confirmed bot polling starts successfully and token is valid (`getMe` check passed).

### 5) DevOps and Deployment Scaffold

- Added nginx reverse proxy config + nginx Dockerfile.
- Added deploy scripts (`deploy/setup.sh`, `deploy/deploy.sh`) and systemd unit (`deploy/learningos-api.service`).
- Added `docker-compose.yml` with local `postgres` and `redis` services.

### 6) Local Sprint 1 Validation

- `docker compose up -d` passed (`postgres`, `redis` running).
- Backend run passed: `/docs` reachable and `/health` returns `{ "status": "ok", "version": "0.1.0" }`.
- Backend tests passed: `4 passed`.
- Bot polling run passed; `/start` processed and WebApp button shown.
- Confirmed Telegram contact and Mini App open flow from bot message.
- For HTTPS Mini App testing, installed tunnel tooling:
  - `ngrok` install succeeded but requires account authtoken.
  - `cloudflared` quick tunnel used as fallback.
- Added tunnel host allowlist in `frontend/vite.config.ts` and corresponding CORS origin in `backend/.env`.

### 7) Frontend WebApp Bootstrap Verification (2026-04-14)

Что сделано:
- Vite + React + TypeScript инициализирован.
- `@twa-dev/sdk` установлен и настроен.
- `src/lib/telegram.ts` — утилиты WebApp SDK.
- `src/lib/api.ts` — axios клиент с `tma` авторизацией.
- Telegram script подключён в `index.html`.
- `npm run build` — OK.
- `npx tsc --noEmit` — OK.
- dev-сервер отвечает на `:5173` — OK.

## [Спринт 2] Дизайн-система
Дата: 2026-04-15
Статус: ✅ завершено

Что сделано:
- src/styles/theme.css — CSS-переменные из Telegram theme params
- src/styles/global.css — базовый reset
- src/hooks/useTelegramTheme.ts — live-обновление темы
- src/components/ui/ — Button, Card, Badge, Typography, Divider
- src/pages/DevKit.tsx — витрина компонентов
- npx tsc --noEmit — OK
- npm run build — OK
- dev-сервер :5173 — OK

Порядок теста (Telegram):
1. Проверка сборки фронта: `npx tsc --noEmit` и `npm run build`.
2. Запуск backend: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
3. Проверка backend: `GET /health` => `{"status":"ok","version":"0.1.0"}`.
4. Запуск frontend: `npm run dev` (порт `5173`).
5. Проверка frontend: `curl http://localhost:5173` => HTTP `200`.
6. Поднятие HTTPS-туннелей `cloudflared` для `:8000` и `:5173`.
7. Привязка WebApp URL в боте к frontend tunnel и проверка открытия Mini App из `/start`.
8. Проверка в Telegram: загрузка DevKit-экрана и применение theme params (light/dark).
9. Завершение теста: остановка `uvicorn`, `vite`, `cloudflared`, `bot`.

## [Спринт 2] Навигация и экраны
Дата: 2026-04-15
Статус: ✅ завершено

Что сделано:
- src/router.tsx — react-router-dom, 4 маршрута
- src/components/layout/ — Layout, BottomNav, BottomTab
- src/components/ui/Skeleton.tsx — shimmer-анимация
- src/pages/ — TodayPage, RoadmapPage, KnowledgePage, AnalyticsPage
- Bottom tabs с SVG-иконками и active-состоянием
- safe-area-inset-bottom для iPhone
- npx tsc --noEmit — OK
- npm run build — OK

## Current Follow-ups

- Replace placeholder API endpoints (plans/focus/ask/analytics/users update/delete) with real logic.
- For stable Mini App testing, replace temporary tunnel URL with permanent HTTPS domain.
- Keep backend/bot/frontend `.env` values aligned for production.
- Add CI pipeline for tests + lint and formal release workflow.

## Notes

- On Windows, `bot` pinned dependencies install reliably with Python 3.12.
- Root and service-level Makefiles currently use Unix-style `.venv/bin/...` commands and need Windows-specific alternatives for direct `make` usage on PowerShell.