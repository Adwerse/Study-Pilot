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

## Telegram Setup
1. Create or select the bot in BotFather.
2. Set `BOT_TOKEN` and `TELEGRAM_BOT_TOKEN`.
3. Deploy the frontend over HTTPS.
4. Configure the Mini App/Web App URL in BotFather to `MINI_APP_URL`.
5. Ensure backend `ALLOWED_ORIGINS` includes the exact Mini App origin.

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
- Keep the previous container image or Railway deployment available.
- Roll back the app before rolling back database changes.
- SQL migrations in this repo are forward-only; restore from a database backup if a schema rollback is required.
- After rollback, verify `/health`, `/health/ready`, bot start, Mini App load, auth, roadmap, upload, RAG, and analytics.

## Common Issues
- `Invalid initData`: check Telegram bot token consistency between BotFather and backend.
- CORS failures: verify `ALLOWED_ORIGINS` exactly matches the Mini App HTTPS origin.
- Readiness `vector_store=not_ready`: run migrations and confirm `CREATE EXTENSION vector`.
- RAG upload stuck or failed: check `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, and document size/type.
- Weekly digest not sending: check `WEEKLY_DIGEST_ENABLED`, bot token, user Telegram ids, and worker logs.
