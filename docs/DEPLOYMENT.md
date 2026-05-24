# StudyPilot Deployment

## Required Services
- PostgreSQL 16 with the `pgvector` extension.
- Backend FastAPI service.
- Frontend static Mini App service.
- Telegram bot service.
- HTTPS reverse proxy or platform routing for the app and API domains.

## Required Environment
Use `.env.production.example` as the source of truth. Production must set:

- `APP_ENV=production`, `TESTING=false`, `TEST_AUTH_ENABLED=false`
- `DATABASE_URL`
- `SECRET_KEY`
- `BOT_TOKEN` / `TELEGRAM_BOT_TOKEN`
- `MINI_APP_URL`
- `ALLOWED_ORIGINS`
- `OPENAI_API_KEY`
- `LLM_PROVIDER`, `TENSORIX_API_KEY` when `LLM_PROVIDER=tensorix`
- `VECTOR_STORE_PROVIDER=pgvector`
- `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`
- `INTERNAL_JOBS_SECRET`

Never put secrets in the frontend bundle. Only `VITE_API_BASE_URL` should be exposed to the frontend.

## Database And Migrations
Enable pgvector before document/RAG use:

```sh
CREATE EXTENSION IF NOT EXISTS vector;
```

For Docker production, the `migrate` service runs `deploy/run-migrations.sh` automatically.

Manual migration command:

```sh
for f in backend/migrations/*.sql; do psql "$DATABASE_URL_SYNC" -v ON_ERROR_STOP=1 -f "$f"; done
```

Use a sync PostgreSQL URL for `psql`, for example:

```sh
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/learning_os
```

## Docker Production
Build and start the stack:

```sh
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d
```

Stop it:

```sh
docker compose -f docker-compose.prod.yml down
```

Destroy local production data only when intentionally resetting:

```sh
docker compose -f docker-compose.prod.yml down -v
```

The production compose stack includes Postgres, migrations, backend, frontend, bot, and Caddy.

## Render Blueprint
This repo includes a `render.yaml` Blueprint for Render:

- `studypilot-api`: FastAPI web service on a paid `starter` instance.
- `studypilot-bot`: Telegram bot polling worker on a paid `starter` instance.
- `studypilot-web`: static Vite frontend.
- `studypilot-postgres`: PostgreSQL 16 database on `basic-256mb`.

The paid API and bot instances are intentional. Render free web services can sleep,
and Render does not support free background workers. The database is also paid so
production data does not expire with the free Postgres lifecycle.

Before applying the Blueprint, commit and push `render.yaml` to the Git remote. Then open:

```txt
https://dashboard.render.com/blueprint/new?repo=https://github.com/Adwerse/Learnify
```

Fill the environment variables marked `sync: false` in Render:

- `BOT_TOKEN`
- `MINI_APP_URL`
- `ALLOWED_ORIGINS`
- `OPENAI_API_KEY`
- `TENSORIX_API_KEY` when `LLM_PROVIDER=tensorix`
- `VITE_API_BASE_URL`

Use these URL values on the first Blueprint sync, then verify them against the actual
service URLs Render assigns:

- `MINI_APP_URL=https://studypilot-web.onrender.com`
- `ALLOWED_ORIGINS=https://studypilot-web.onrender.com`
- `VITE_API_BASE_URL=https://studypilot-api.onrender.com`

If Render assigns different subdomains, update the service environment variables and
redeploy the affected services. `VITE_API_BASE_URL` is embedded at frontend build time,
so redeploy `studypilot-web` after changing it.

The API service runs SQL migrations in Render's `preDeployCommand` with
`backend/scripts/run_migrations.py`. The backend accepts Render PostgreSQL URLs and
normalizes them for SQLAlchemy asyncpg.

Render deployment checks:

```sh
curl https://studypilot-api.onrender.com/health
curl https://studypilot-api.onrender.com/health/ready
```

Expected readiness shape:

```json
{"status":"ready","checks":{"database":"ok","vector_store":"ok"}}
```

## Telegram Setup
1. Create or select the bot in `@BotFather` and copy the bot token.
2. Set `BOT_TOKEN` on both Render services: `studypilot-api` and `studypilot-bot`.
3. Set `MINI_APP_URL` on both services to the frontend HTTPS URL.
4. Set backend `ALLOWED_ORIGINS` to the exact frontend HTTPS origin.
5. In `@BotFather`, configure the bot's Mini App/Menu Button URL to `MINI_APP_URL`.
6. Open the bot in Telegram, send `/start`, click `Open Learning OS`, and create a small test roadmap.

## Service Commands
Backend local:

```sh
cd backend
uvicorn app.main:app --reload
```

Frontend local:

```sh
cd frontend
npm run dev
```

Bot local:

```sh
cd bot
python main.py
```

## Health Checks
- Liveness: `GET /health`
- Readiness: `GET /health/ready`

Readiness checks database connectivity and pgvector availability. It returns `503` when the app is not ready.

## Rollback Notes
- Keep the previous Render deploy or container image available.
- Roll back the app before rolling back database changes.
- SQL migrations in this repo are forward-only; restore from a database backup if a schema rollback is required.
- After rollback, verify `/health`, `/health/ready`, bot start, Mini App load, auth, roadmap, upload, RAG, and analytics.

## Common Issues
- `Invalid initData`: check Telegram bot token consistency between BotFather and backend.
- CORS failures: verify `ALLOWED_ORIGINS` exactly matches the Mini App HTTPS origin.
- Readiness `vector_store=not_ready`: run migrations and confirm `CREATE EXTENSION vector`.
- RAG upload stuck or failed: check `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, and document size/type.
- Weekly digest not sending: check `WEEKLY_DIGEST_ENABLED`, bot token, user Telegram ids, and worker logs.
