# StudyPilot Monitoring

## Health Endpoints
- `GET /health` verifies the backend process is alive.
- `GET /health/ready` verifies database and pgvector readiness.
- Frontend Docker image exposes `/health`.

Readiness should return `200` before traffic is routed. Treat `503` as not deploy-ready.

## Logs To Watch
- App startup and shutdown.
- Readiness/database connection failures.
- Telegram `sendMessage` failures.
- RAG embedding, vector search, and answer generation failures.
- Document ingest failures.
- Weekly digest worker failures.
- Weekly review generation or apply failures.
- Any spike in request logs with `status_code=5xx`.

Backend request logs include request id, method, path, status code, and duration. They intentionally do not log request bodies, uploaded document content, API keys, or full LLM prompts.

## Error Categories
- DB errors: connection refused, migration missing, transaction failures.
- Telegram errors: invalid bot token, blocked bot, Telegram HTTP errors.
- AI provider errors: OpenAI/Tensorix auth failure, timeout, malformed model response.
- Vector store errors: pgvector extension missing, embedding dimension mismatch, vector query failure.
- Ingest failures: unsupported file type, empty document, oversized upload, embedding failure.

## Suggested Alerts
- Backend `/health` down for more than 2 minutes.
- `/health/ready` returns `503`.
- 5xx rate exceeds normal baseline for 5 minutes.
- Repeated Telegram send failures.
- Repeated document ingest failures.
- Weekly digest job fails or processes zero users unexpectedly.
- Weekly Review apply failures or repeated conflicts.

## Manual Checks After Deploy
1. Open the Mini App on a mobile Telegram viewport.
2. Confirm `/health` and `/health/ready` return `200`.
3. Confirm Telegram auth works and `/api/v1/users/me` returns the current user.
4. Generate or load a roadmap.
5. Open Today and start/end a focus session.
6. Upload a small `.txt` file and ask a RAG question.
7. Open Analytics and verify empty or seeded charts render.
8. Generate a Weekly Review from the backend API if reviewing a release candidate.

## Privacy And Secrets
- Do not log bot tokens, API keys, auth headers, uploaded document bodies, or full prompts.
- Debug logging should stay off in production.
- Test auth and fake providers must only run with `APP_ENV=test` and `TESTING=true`.
