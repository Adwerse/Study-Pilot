# Learning OS Work Log

Last updated: 2026-05-19

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

## [Sprint 3] Today Screen
Date: 2026-04-20
Status: completed

What was done:
- `src/hooks/useTodayPlan.ts` with parallel requests plus sessionStorage progress.
- `src/components/today/StageProgress.tsx` with the stage progress bar and 4 tests.
- `src/components/today/FocusBlockCard.tsx` with the block card, 4 states, and 5 tests.
- `src/components/today/DailyNote.tsx` with the daily note.
- `src/pages/TodayPage.tsx` with the full screen and 4 states.
- `npx tsc --noEmit` passed.
- `npm run build` passed.
- `npm run test` passed.

## [Sprint 3] Roadmap To Daily Coach Link
Date: 2026-04-20
Status: completed

What was done:
- `backend/app/api/plans.py` saves roadmap output in the runtime store via `POST /plans`.
- `backend/app/api/plans.py` returns the current saved plan via `GET /plans/current`.
- `backend/app/api/plans.py` generates Daily Coach output from the real current stage via `GET /plans/current/today`.
- `backend/app/api/focus.py` implements `POST /focus/start`, `POST /focus/end`, and `GET /focus/history`.
- `backend/app/repositories/runtime_store.py` adds user-scoped in-memory state for plans, stages, and focus history.
- `backend/app/schemas/focus_session.py` adds the `FocusSession` schema.
- `backend/tests/test_plan_persistence.py` adds tests for roadmap persistence and focus-history use in today-plan generation.
- `pytest tests/test_plan_persistence.py tests/test_daily_coach.py -v` passed with 6 tests.

Current implementation limit:
- Roadmap/focus persistence is implemented in process memory through the runtime store.
- Backend restarts clear the state; durable PostgreSQL persistence remains the next step.

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

## [Sprint 4] Focus Agent
Date: 2026-04-23
Status: completed

What was done:
- `app/models/focus_log.py` with ORM `FocusLog`.
- `app/schemas/focus_log.py` with `FocusSessionStart`, `FocusSessionEnd`, and `FocusSessionRead`.
- `app/repositories/user_repository.py` with `get_or_create_by_telegram_id`.
- `app/repositories/focus_repository.py` with start, end, active, history, and today helpers.
- `app/agents/focus.py` with `FocusAgent` messages, break logic, and reminders.
- `app/api/focus.py` with 4 endpoints: start, end, active, and history.
- `app/api/focus.py` resolves `user_id` through `UserRepository`, not through `UUID(int=telegram_id)`.
- `tests/test_focus_agent.py` with 5 unit tests.
- `tests/test_focus_repository.py` with 3 unit tests.
- 8 tests passed.

Known limitations:
- Pause is not implemented because it was out of scope for Sprint 4.
- Bot notifications remain TODO and should be connected after bot/backend integration.

## [Sprint 4] Pomodoro Timer
Date: 2026-04-25
Status: completed

What was done:
- `src/hooks/usePomodoro.ts` with 5s polling plus a local tick every second.
- `src/lib/api.ts` adds `apiClient.getActiveSession`.
- `src/components/timer/CircularTimer.tsx` with the SVG timer and 4 tests.
- `src/components/timer/DifficultyPicker.tsx` with the rating bottom sheet and 3 tests.
- `src/components/timer/StartForm.tsx` with the topic form and 3 tests.
- `src/components/timer/PomodoroScreen.tsx` with the state orchestrator.
- `src/pages/TodayPage.tsx` integrates the fullscreen overlay for active sessions.
- `npx tsc --noEmit` passed.
- `npm run build` passed.
- `npm run test` passed with 10 new tests and 27 total tests.

Architecture decision:
  Polling was chosen instead of WebSocket because it is simpler to deploy and sufficient for the Pomodoro UX.
  The timer is calculated on the frontend from the database-backed `started_at` value.

## [Sprint 4] Focus API Backend
Date: 2026-04-29
Status: completed

What was done:
- Checked compatibility with the current backend architecture before implementation.
- Kept the existing stack and patterns: FastAPI, async SQLAlchemy ORM, raw SQL migrations, current Telegram `get_current_user` dependency, async repositories, and `/api/v1` routers.
- Extended `backend/app/models/focus_log.py` from the old `completed`/`duration_minutes` shape to the Sprint 4 contract:
  - `status`: `active`, `completed`, `cancelled`
  - `plan_id`
  - `plan_stage_id`
  - `planned_duration_minutes`
  - `actual_duration_seconds`
  - `notes`
  - `created_at`
  - `updated_at`
- Added compatibility aliases on the ORM model:
  - `stage_id` -> `plan_stage_id`
  - `completed` -> `status == "completed"`
  - `duration_minutes` -> derived from `actual_duration_seconds` or planned duration
- Added `backend/migrations/006_update_focus_log_sprint4.sql`.
- Added PostgreSQL partial unique index `ux_focus_log_one_active_per_user` to guarantee at most one `active` focus session per user.
- Updated `backend/app/schemas/focus_log.py` with `FocusSessionStart`, `FocusSessionEnd`, `FocusSessionRead`, and `FocusHistoryResponse`.
- Added `backend/app/services/focus_service.py` for business rules:
  - reject second active session with `409`
  - end by explicit `session_id` or current active session
  - reject ending another user's session
  - reject already ended sessions with `409`
  - calculate `actual_duration_seconds` with timezone-aware UTC datetimes
  - validate owned `plan_id` / `plan_stage_id`
- Updated `backend/app/repositories/focus_repository.py` for create, finish, active lookup, paginated history, and owned plan/stage lookups.
- Updated `backend/app/api/focus.py`:
  - `POST /focus/start`
  - `POST /focus/end`
  - `GET /focus/history`
  - kept `GET /focus/active` for the current frontend polling flow
- Added backend tests in `backend/tests/test_focus_service.py`.
- Cleaned stale unused imports in `backend/tests/test_focus_repository.py`.

Checks:
- `python -m ruff check app tests` passed.
- `python -m ruff format --check` passed for changed files.
- `python -m pytest tests/test_focus_repository.py tests/test_focus_service.py -q` passed with `11 passed`.
- Full `pytest tests -q` was blocked locally when PostgreSQL was not running; after Docker/Postgres startup, the app was able to run against the dev database.

## [Sprint 5] RAG Document Ingest Backend
Date: 2026-05-02
Status: completed

What was done:
- Analyzed the existing backend architecture before implementation: FastAPI routers, async SQLAlchemy ORM, raw SQL migrations, Telegram Mini App auth through `get_current_user`, repository/service split, settings, and current AI client usage.
- Added user-scoped document APIs under `/api/v1/documents`:
  - `POST /documents/upload`
  - `GET /documents`
  - `GET /documents/{document_id}`
- Added `backend/app/models/document.py` with ORM models:
  - `Document`
  - `DocumentChunk`
- Added `backend/migrations/008_create_documents.sql`:
  - `documents`
  - `document_chunks`
  - `pgvector` extension
  - user/document indexes
  - cosine vector index for future RAG search
- Added `backend/app/schemas/document.py` with upload, list, and detail response schemas.
- Added `backend/app/repositories/document_repository.py` for create, list, owned lookup, chunk replacement, retry cleanup, and failed-status updates.
- Added `DocumentTextExtractor`:
  - supports `.txt`, `.md`, `.pdf`
  - validates extension and content type
  - decodes UTF-8 text files
  - extracts PDF text page-by-page with `pypdf`
  - preserves `page_number` metadata for PDF chunks
  - raises domain errors for unsupported, empty, or failed extraction cases
- Added `DocumentChunker`:
  - configurable char-based chunk size and overlap
  - paragraph/sentence-aware breakpoints
  - max chunks guard
  - chunk metadata with `filename`, `source_type`, and optional `page_number`
- Added `EmbeddingService` using OpenAI embeddings through settings:
  - `OPENAI_API_KEY`
  - `EMBEDDING_MODEL`
  - `EMBEDDING_DIMENSIONS`
  - batched `embed_texts`
  - provider errors are logged and surfaced to ingest safely
- Added `VectorIndexService` abstraction over the current pgvector-backed storage.
- Added `DocumentIngestService` orchestration:
  - set status to `processing`
  - extract text
  - chunk text
  - generate embeddings
  - upsert chunks and vectors
  - set status to `ready`
  - on failure set status to `failed` with a sanitized error message
  - retry-friendly cleanup so repeated ingest does not duplicate chunks
- Added settings:
  - `DOCUMENT_MAX_FILE_SIZE_BYTES`
  - `DOCUMENT_CHUNK_SIZE_CHARS`
  - `DOCUMENT_CHUNK_OVERLAP_CHARS`
  - `DOCUMENT_MAX_CHUNKS`
  - `EMBEDDING_MODEL`
  - `EMBEDDING_DIMENSIONS`
- Added dependencies:
  - `python-multipart`
  - `pypdf`
  - `pgvector`
- Updated `.env.example` with document ingest and embedding settings.

Checks:
- Installed backend dependencies from `backend/requirements.txt` into `backend/.venv`.
- `python -m pytest tests/test_document_processing_services.py tests/test_document_ingest_service.py tests/test_documents_api.py -q` passed with `16 passed`.
- `python -m ruff check` passed for changed backend files and new tests.
- `python -m ruff format --check` passed for changed backend files and new tests.
- Full `python -m pytest tests -q` result: `55 passed`, `2 skipped`, `1 failed`; the failing pre-existing `test_plan_persistence.py` case was blocked by local PostgreSQL connection refusal, not by the new ingest pipeline.

## [Sprint 5] RAG Agent
Date: 2026-05-03
Status: completed

What was done:
- Checked compatibility with the current backend architecture before implementation: FastAPI routers, Telegram Mini App auth dependency, async SQLAlchemy repositories, document ingest pipeline, pgvector-backed chunks, settings, logging, and existing tests.
- Replaced the placeholder `POST /api/v1/ask` with a production RAG endpoint using `response_model`.
- Added `backend/app/schemas/rag.py` with validated request and response schemas:
  - `question`
  - optional `document_ids`
  - `top_k`
  - `rerank_top_k`
  - answer, sources, rewritten query, and confidence in the response.
- Added `backend/app/services/rag_agent.py` as the orchestrator:
  - validate user/document access
  - rewrite query
  - embed rewritten query
  - vector search over user-scoped chunks
  - rerank results
  - generate grounded answer
  - return cited sources and confidence.
- Added `QueryRewriter`:
  - uses the existing OpenAI-compatible LLM client
  - keeps the user's language
  - limits rewritten query length
  - falls back to the original question if rewrite fails.
- Added `VectorSearchService` over the existing pgvector storage:
  - searches `document_chunks.embedding`
  - filters by `user_id`
  - optionally filters by `document_ids`
  - joins document title and filename for source metadata.
- Added `Reranker`:
  - lightweight lexical overlap scoring
  - combines vector and lexical scores
  - falls back to vector order if an external/provider reranker fails.
- Added `AnswerGenerator`:
  - strictly grounded system prompt
  - JSON response parsing
  - citations in `[1]`, `[2]` format
  - confidence heuristic
  - graceful provider error propagation.
- Extended `DocumentRepository` with:
  - `list_by_ids_for_user`
  - `count_ready_by_user`
- Added RAG settings:
  - `RAG_REWRITE_MODEL`
  - `RAG_ANSWER_MODEL`
  - `RAG_TOP_K_DEFAULT`
  - `RAG_RERANK_TOP_K_DEFAULT`
  - `RAG_MIN_SCORE_THRESHOLD`
  - `RAG_MAX_CONTEXT_CHARS`
  - `RAG_SNIPPET_CHARS`
- Updated `.env.example` with the new RAG settings.
- Added `backend/tests/test_rag_agent.py` covering API validation, ownership checks, no-context behavior, query rewrite fallback, vector search filters, rerank ordering/fallback, answer generation, snippets, citations, and source ordering.

Behavior:
- If no ready documents or no relevant chunks are found, `/ask` returns a truthful low-confidence answer with `sources: []`.
- If `document_ids` contains another user's document, the endpoint returns `404`.
- Embedding, vector search, and answer-generation provider errors are surfaced as `503`.
- The RAG response only includes sources based on chunks selected for the generated answer.

Checks:
- Installed backend dependencies from `backend/requirements.txt` into the existing local `.venv` so tests and lint could run.
- `python -m ruff check app tests` passed.
- `python -m ruff format --check` passed for changed RAG/backend files and the new RAG tests.
- `python -m pytest tests/test_rag_agent.py -q` passed with `18 passed`.
- `python -m pytest tests/test_rag_agent.py tests/test_documents_api.py tests/test_document_ingest_service.py tests/test_document_processing_services.py -q` passed with `34 passed`.
- `python -m pytest tests/ -q -k "not test_daily_plan_uses_current_stage_and_focus_history"` passed with `73 passed`, `2 skipped`, `1 deselected`.
- Full `python -m pytest tests/ -q` result: `73 passed`, `2 skipped`, `1 failed`; the remaining failure is the pre-existing DB-dependent `test_daily_plan_uses_current_stage_and_focus_history`, blocked locally by PostgreSQL connection refusal, not by the RAG Agent.

Known follow-up:
- Frontend `KnowledgePage` and `apiClient` still point at the legacy `/api/v1/ask/documents` placeholder routes for document upload/list/delete. They need to be switched to the real `/api/v1/documents` endpoints and wired to `POST /api/v1/ask`.

## [Sprint 5] RAG API
Date: 2026-05-04
Status: completed

What was done:
- Audited the existing Sprint 5 backend before implementation: document models, ingest pipeline, `RAGAgent`, pgvector-backed search, schemas, routers, auth dependency, and tests.
- Kept routers thin and added service-layer integration:
  - `DocumentService`
  - `RAGService`
- Updated `POST /api/v1/ask`:
  - uses `AskRequest` / `AskResponse`
  - validates `question`, `top_k`, `rerank_top_k`, and `document_ids`
  - rejects `rerank_top_k > top_k` with `422`
  - maps foreign or missing `document_ids` to `404`
  - maps RAG provider/vector errors to `503`
  - keeps no-context / no-relevant-chunks behavior as a truthful low-confidence answer.
- Updated RAG source alignment so response `sources` follow citation order in the answer.
- Updated `GET /api/v1/documents`:
  - user-scoped only
  - `limit` / `offset`
  - `status` filter
  - optional case-insensitive `q` search over title and filename
  - `created_at DESC`
  - no chunks or full text in the response
  - safe short `error_message` output.
- Added `DELETE /api/v1/documents/{document_id}`:
  - user-scoped lookup by `user_id + document_id`
  - returns `404` for missing or foreign documents
  - calls `VectorIndexService.delete_document(document_id, user_id)`
  - removes chunks/vector entries before deleting the document
  - returns `503` and keeps the document in DB if vector cleanup fails
  - returns `204 No Content` on success.
- Removed obsolete placeholder document routes from `backend/app/api/ask.py`.
- Extended `DocumentRepository` with escaped `q` search and physical document deletion.
- Added focused tests for ask validation/errors, document listing filters, user isolation, deletion cleanup, vector cleanup failures, repeated delete behavior, and source ordering.

Checks:
- `python -m pytest tests/test_documents_api.py tests/test_rag_agent.py -q` passed with `33 passed`.
- `python -m ruff check` passed for changed backend files and focused tests.
- `python -m ruff format --check` passed for changed backend files and focused tests.
- Full `python -m pytest tests -q` result: `81 passed`, `2 skipped`, `1 failed`; the remaining failure is the DB-dependent `test_daily_plan_uses_current_stage_and_focus_history`, blocked locally by PostgreSQL connection refusal, not by the RAG API changes.

Known follow-up:
- Frontend `KnowledgePage` and `apiClient` still need to be switched from `/api/v1/ask/documents` to the real `/api/v1/documents` endpoints and updated for the typed RAG response shape.

## [Sprint 5] Knowledge Base Frontend
Date: 2026-05-05
Status: completed

What was done:
- Checked compatibility with the current frontend and backend before implementation: Vite + React + TypeScript, existing axios API client, local hooks pattern, Telegram theme CSS variables, `/knowledge` route, bottom navigation, UI primitives, and Sprint 5 backend schemas/endpoints.
- Replaced the placeholder `KnowledgePage` with a full Telegram Mini App knowledge base screen:
  - upload block for PDF, TXT, and MD files up to 10 MB
  - materials list with processing, ready, and failed statuses
  - document search, status filter, pagination, and empty/loading/error states
  - delete flow with confirmation before removing a document
  - ready-document selection for scoped RAG search
  - RAG chat with disabled state when no ready documents exist
  - assistant answers with confidence indicator and compact source cards.
- Updated `frontend/src/lib/api.ts`:
  - `uploadDocument(file, metadata)`
  - `getDocuments(params)`
  - `deleteDocument(documentId)`
  - `askQuestion(payload)`
  - switched from the legacy `/api/v1/ask/documents` placeholder routes to `/api/v1/documents` and `/api/v1/ask`.
- Updated `frontend/src/types/api.ts` with Sprint 5 document and RAG response types.
- Added `frontend/src/hooks/useKnowledge.ts`:
  - `useDocuments`
  - `useUploadDocument`
  - `useDeleteDocument`
  - `useAskQuestion`
- Added `frontend/src/utils/knowledgeFormatters.ts` for file size, status, date/time, confidence, and safe displayed text formatting.
- Updated the bottom tab label from `Knowledge` to `Knowledge Base` and guarded tab text against overflow.
- Added frontend tests for API methods, hooks, formatters, and the main Knowledge Base UI flows.

Checks:
- `npm test` passed with `61 passed`.
- `npm run build` passed.
- Local Vite dev server started and responded with HTTP `200` at `http://localhost:5173/`.

## [Sprint 5] Knowledge Upload Dev Fix
Date: 2026-05-05
Status: completed

What was done:
- Investigated the Mini App failure where document upload showed `Unable to upload file` and the materials list also failed to load.
- Confirmed the root cause was environment/database availability, not the selected `.md` file:
  - local PostgreSQL was not listening on `127.0.0.1:5432`
  - Docker Desktop was initially not running
  - the active dev database did not yet have `documents`, `document_chunks`, or the `vector` extension.
- Started local PostgreSQL with the pgvector-compatible image from `docker-compose.yml`:
  - `pgvector/pgvector:pg16`
- Applied `backend/migrations/008_create_documents.sql` to the dev database.
- Restarted the FastAPI backend so it used the current code and the now-available database.
- Updated `backend/app/api/documents.py` so upload database failures return a clear `503 Database unavailable` instead of surfacing as an unclear upload failure.
- Updated `frontend/src/lib/api.ts` to let the browser/axios set the multipart `Content-Type` boundary for `FormData` uploads.
- Updated `KnowledgePage` error mapping so database downtime is shown as a human-readable database availability message rather than a generic RAG/upload error.
- Removed smoke-test documents/users created during manual verification.

Checks:
- `GET /api/v1/documents` with valid Telegram initData returned `200` and a document list payload.
- `POST /api/v1/documents/upload` with a markdown file returned `status: ready`.
- Upload through the frontend Cloudflare tunnel also returned `status: ready`.
- `python -m pytest tests/test_documents_api.py -q` passed with `12 passed`.
- `npm test -- --run src/lib/api.test.ts src/pages/KnowledgePage.test.tsx` passed with `12 passed`.

## Dev Runbook: Bot + Mini App With HTTP Tunnels
Date: 2026-04-29
Status: current dev procedure

Goal:
- Run the Telegram bot in polling mode.
- Serve the Mini App through an HTTPS frontend tunnel.
- Serve FastAPI through an HTTPS backend tunnel.
- Make frontend API calls work from Telegram WebView by aligning `VITE_API_BASE_URL` and backend `ALLOWED_ORIGINS`.

Prerequisites:
- Docker Desktop is running.
- `cloudflared` is installed.
- Backend virtualenv exists at `backend/.venv`.
- Bot virtualenv exists at `bot/.venv`.
- Frontend dependencies are installed in `frontend/node_modules`.
- Root `.env` contains valid `BOT_TOKEN`, `MINI_APP_URL`, database settings, and API keys as needed.

1. Start local infrastructure:

```powershell
docker compose up -d postgres redis
docker compose ps
```

2. Apply the Sprint 4 focus migration if the dev database already exists:

```powershell
Get-Content backend\migrations\006_update_focus_log_sprint4.sql |
  docker exec -i learning-os-postgres psql -U postgres -d learning_os -v ON_ERROR_STOP=1
```

For a clean database, run all migration files in order instead.

3. Start the backend locally:

```powershell
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

Verify:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
```

4. Create the backend HTTPS tunnel:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Copy the printed URL, for example:

```text
https://<backend-tunnel>.trycloudflare.com
```

Verify:

```powershell
Invoke-WebRequest -UseBasicParsing https://<backend-tunnel>.trycloudflare.com/health
```

5. Start the frontend with the backend tunnel as API base URL:

```powershell
cd frontend
$env:VITE_API_BASE_URL = "https://<backend-tunnel>.trycloudflare.com"
npm run dev -- --host 127.0.0.1 --port 5173
```

6. Create the frontend HTTPS tunnel:

```powershell
cloudflared tunnel --url http://127.0.0.1:5173
```

Copy the printed URL, for example:

```text
https://<frontend-tunnel>.trycloudflare.com
```

Verify:

```powershell
Invoke-WebRequest -UseBasicParsing https://<frontend-tunnel>.trycloudflare.com
```

7. Restart the backend with the frontend tunnel allowed by CORS.

Stop the backend process, then start it again:

```powershell
cd backend
$env:ALLOWED_ORIGINS = '["http://localhost:5173","http://127.0.0.1:5173","https://<frontend-tunnel>.trycloudflare.com"]'
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

Verify CORS preflight:

```powershell
$headers = @{
  Origin = "https://<frontend-tunnel>.trycloudflare.com"
  "Access-Control-Request-Method" = "GET"
  "Access-Control-Request-Headers" = "authorization"
}

Invoke-WebRequest `
  -UseBasicParsing `
  -Method Options `
  -Uri "https://<backend-tunnel>.trycloudflare.com/api/v1/users/me" `
  -Headers $headers
```

Expected:
- HTTP `200`
- `Access-Control-Allow-Origin` equals the frontend tunnel URL.

8. Start the bot in dev polling mode with the frontend tunnel as Mini App URL:

```powershell
cd bot
$env:MINI_APP_URL = "https://<frontend-tunnel>.trycloudflare.com"
$env:USE_WEBHOOK = "false"
$env:DEBUG = "false"
.\.venv\Scripts\python.exe main.py
```

Expected bot logs:

```text
Polling mode enabled
Start polling
Run polling for bot @Lernify_bot
```

9. Test in Telegram:
- Open `@Lernify_bot`.
- Send `/start`.
- Tap the Mini App button.
- If the Mini App shows `Network Error`, check CORS first:
  - frontend tunnel URL must be present in backend `ALLOWED_ORIGINS`
  - frontend must have been started with `VITE_API_BASE_URL=https://<backend-tunnel>.trycloudflare.com`
  - close and reopen the Telegram Mini App after changing tunnel/env values

Current dev-session example from 2026-04-29:
- Backend tunnel: `https://officers-amend-subjects-barry.trycloudflare.com`
- Frontend tunnel: `https://julian-celebrity-vincent-bon.trycloudflare.com`
- Bot: `@Lernify_bot`
- Note: `trycloudflare.com` quick tunnel URLs are temporary and should not be committed into `.env` as stable values.

## Production Docker Compose
Date: 2026-05-09
Status: prepared

Goal:
- Prepare a self-hosted VPS deployment path for the Telegram Mini App.

What was done:
- Added `docker-compose.prod.yml` for a production-style stack:
  - `postgres` using `pgvector/pgvector:pg16`
  - one-shot `migrate` service
  - FastAPI `backend`
  - polling-mode Telegram `bot`
  - Vite `frontend`
  - `caddy` reverse proxy with automatic HTTPS
- Added `deploy/Caddyfile`:
  - `APP_DOMAIN` proxies to `frontend:4173`
  - `API_DOMAIN` proxies to `backend:8000`
- Added `deploy/run-migrations.sh` with `schema_migrations` tracking so repeated `docker compose up` does not rerun already-applied SQL migrations.
- Added `.env.production.example` with the required production variables.
- Updated `frontend/Dockerfile` to accept `VITE_API_BASE_URL` as a build arg, because Vite embeds it at build time.
- Added `.dockerignore` files for `backend`, `bot`, and `frontend` so local `.env`, virtualenvs, caches, `node_modules`, and build artifacts do not get copied into Docker images.
- Updated `.gitignore` to ignore production env files such as `.env.production`.

Verification:
- `docker compose --env-file .env.production.example -f docker-compose.prod.yml config --quiet` passed.
- Full Docker image build was not run because Docker Desktop was not running locally:
  - `dockerDesktopLinuxEngine` pipe was unavailable.

Run command:

```bash
cp .env.production.example .env.production
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Production notes:
- DNS must point `APP_DOMAIN` and `API_DOMAIN` to the VPS before Caddy can issue certificates.
- BotFather Mini App URL should be `https://APP_DOMAIN`.
- `VITE_API_BASE_URL` changes require rebuilding the frontend image.

## Sprint 6 Weekly Review + Roadmap Recalculation
Date: 2026-05-10
Status: implemented

Goal:
- Add a backend Weekly Review flow that compares planned roadmap progress with actual focus/analytics data and safely proposes roadmap adaptations.

What was done:
- Added `/api/v1/weekly-review` endpoints:
  - `POST /generate`
  - `POST /{review_id}/apply`
  - `GET /history`
- Added `weekly_reviews` persistence with structured JSONB fields for insights, risks, recommendations, metrics, and proposed changes.
- Added nullable `start_date` and `end_date` to `plan_stages` for safe rescheduling.
- Added migration `009_create_weekly_reviews.sql` with stage date backfill and weekly review table/indexes.
- Added `RoadmapProgressAnalyzer` for deterministic planned vs actual progress calculation.
- Added `WeeklyReviewAgent` with LLM-assisted narrative/proposals and a no-LLM fallback path.
- Added `WeeklyReviewService` to orchestrate user-scoped generation, persistence, history, and all-or-nothing safe apply.
- Apply currently mutates only `reschedule_stage`; `split_stage`, `adjust_stage_focus`, and `mark_stage_at_risk` are stored as suggestions.
- Added settings:
  - `WEEKLY_REVIEW_AI_ENABLED`
  - `WEEKLY_REVIEW_MODEL`

Safety notes:
- All plan/review queries are scoped by `user_id`.
- LLM output is validated before persistence.
- LLM cannot directly update the database.
- Review storage keeps only final outputs, not chain-of-thought or raw large prompts.
- A review cannot be applied twice.
- Invalid apply rolls back the transaction.

Tests:
- Added analyzer tests for behind/ahead detection, missing planned focus, zero stages, progress percent, and completed-only focus minutes.
- Added agent tests for LLM fallback, invalid JSON fallback, unsafe change filtering, invalid stage IDs, deterministic metrics, and insufficient-data review.
- Added service/apply tests for safe reschedule, invalid stage rollback, split-stage non-apply, double-apply conflict, and rollback on failed apply.
- Added API tests for generate, active-plan fallback behavior, foreign plan/review rejection, apply, conflict handling, invalid timezone, and user-scoped history.

Verification:
- `python -m pytest tests/test_roadmap_progress_analyzer.py tests/test_weekly_review_agent.py tests/test_weekly_review_service.py tests/test_weekly_review_api.py -q` passed: 25 tests.
- `python -m pytest tests/test_plan_repository.py tests/test_analytics_metrics_service.py tests/test_analytics_api.py -q` passed: 17 tests.
- `python -m ruff check app tests/test_roadmap_progress_analyzer.py tests/test_weekly_review_agent.py tests/test_weekly_review_service.py tests/test_weekly_review_api.py` passed.
- A broader run including `tests/test_plan_persistence.py` hit local PostgreSQL `ConnectionRefusedError` during an existing `/focus/start` path because the local DB was unavailable.

## Sprint 6 Analytics Screen
Date: 2026-05-14
Status: implemented

Goal:
- Add the frontend Analytics screen for Sprint 6 using the existing StudyPilot Telegram Mini App architecture.

What was done:
- Integrated the Analytics screen at `/analytics` with the existing bottom navigation tab.
- Added day/week period switching with today/yesterday, current/previous week shortcuts, arrow navigation, and disabled future navigation.
- Added API client coverage for:
  - `GET /api/v1/analytics/daily`
  - `GET /api/v1/analytics/weekly`
- Added analytics TypeScript contracts for period, metrics, topic focus, daily breakdown, report responses, params, and data quality.
- Added `useDailyAnalytics` and `useWeeklyAnalytics` hooks with loading/isLoading, error, refetch, response validation, and stale request cancellation via `AbortController`.
- Added compact summary cards for focus minutes, sessions, streak, and completion rate.
- Added lightweight CSS/SVG-free visualizations:
  - weekly focus bar chart;
  - weekly sessions bar chart;
  - 7-day activity heatmap;
  - topic progress list.
- Added Best Focus Hours chips and AI report/recommendations with data quality labels.
- Added empty, loading, and error/retry states without raw backend error output.
- Added date and formatting helpers, including Monday-based week starts and API `YYYY-MM-DD` formatting.

Quality notes:
- Charts handle empty and zero-value breakdowns without division by zero.
- UI uses existing components, CSS variables, and Telegram theme params.
- No heavy chart dependency was added.
- No `dangerouslySetInnerHTML` is used.
- Today, Roadmap, Focus/Pomodoro, and Knowledge Base navigation remained untouched.

Verification:
- `npm test` passed: 17 test files, 81 tests.
- `npm run build` passed.
- Vite dev server started at `http://127.0.0.1:5173/analytics`.

## Sprint 6 Weekly Telegram Digest
Date: 2026-05-18
Status: implemented

Goal:
- Add an automatic weekly Telegram digest that sends StudyPilot users a concise weekly learning report every Sunday.

What was done:
- Added migration `011_create_weekly_digest_deliveries.sql`:
  - `users.timezone`;
  - `users.notifications_enabled`;
  - `users.weekly_digest_enabled`;
  - `weekly_digest_deliveries` with delivery status, Telegram metadata, safe error storage, timestamps, and unique `(user_id, week_start, week_end)` duplicate prevention.
- Added `WeeklyDigestDelivery` SQLAlchemy model and exported it through the models package.
- Added weekly digest schemas/dataclasses for digest period, report, process result, and per-user delivery result.
- Added `WeeklyDigestRepository` with candidate listing, delivery lookup, pending creation, row-lock claiming, failed retry support, and sent/failed/skipped status transitions.
- Added `WeeklyDigestService` using the existing backend service architecture:
  - calculates real weekly metrics via `AnalyticsMetricsService`;
  - generates narrative via `AnalyticsAgent`;
  - uses existing Weekly Review data where available;
  - generates draft Weekly Review only with `apply_changes=False`;
  - never auto-applies roadmap changes;
  - skips active-plan users with zero completed focus sessions for the week;
  - continues processing after per-user failures.
- Added `WeeklyDigestFormatter` for concise plain-text Telegram messages, with optional sections, low-data-quality note, and message length cap.
- Sends through the existing `TelegramService.send_message` method with no Markdown parse mode.
- Adds a WebApp inline keyboard button to `${MINI_APP_URL}/analytics` when `MINI_APP_URL` is configured.
- Added `weekly_digest_worker_loop` and wired it into FastAPI lifespan next to the existing notification worker.
- Added settings and env examples:
  - `WEEKLY_DIGEST_ENABLED`;
  - `WEEKLY_DIGEST_DAY`;
  - `WEEKLY_DIGEST_HOUR`;
  - `WEEKLY_DIGEST_POLL_INTERVAL_SECONDS`;
  - `WEEKLY_DIGEST_BATCH_LIMIT`.
- Updated analytics and weekly-review routes to persist validated user timezone opportunistically.
- Updated production Docker env wiring for weekly digest and weekly review settings.

Safety notes:
- Telegram sends are mocked in tests; no real Telegram messages are sent.
- Telegram bot token and Mini App URL are never hardcoded.
- Duplicate delivery prevention uses both a database unique constraint and row-lock claiming.
- Failed deliveries are not retried automatically unless `retry_failed=True` is passed.
- Delivery errors are truncated and safe; stack traces and secrets are not stored.

Tests:
- Added formatter tests for required metrics, optional sections, low data quality, raw JSON avoidance, and length cap.
- Added service tests for due-period calculation, UTC fallback, Sunday/hour scheduling, eligibility skips, successful send, failed send, duplicate prevention, failed retry behavior, per-user failure isolation, Weekly Review draft generation, and WebApp reply markup.

Verification:
- `pytest backend/tests/test_weekly_digest_formatter.py backend/tests/test_weekly_digest_service.py -q` passed: 15 tests.
- `pytest backend/tests/test_analytics_api.py backend/tests/test_weekly_review_api.py backend/tests/test_notifications.py backend/tests/test_weekly_digest_formatter.py backend/tests/test_weekly_digest_service.py -q` passed: 39 tests.
- `pytest backend/tests/test_analytics_api.py backend/tests/test_analytics_metrics_service.py backend/tests/test_analytics_agent.py backend/tests/test_weekly_review_api.py backend/tests/test_weekly_review_service.py backend/tests/test_weekly_review_agent.py backend/tests/test_notifications.py backend/tests/test_weekly_digest_formatter.py backend/tests/test_weekly_digest_service.py -q` passed: 63 tests.
- `ruff check backend/app backend/tests/test_weekly_digest_formatter.py backend/tests/test_weekly_digest_service.py` passed.
- `ruff format --check` passed for changed digest files.
- `git diff --check` passed.
- Full backend suite result: 153 passed, 2 skipped, 1 failed because `test_plan_persistence.py::test_daily_plan_uses_current_stage_and_focus_history` could not connect to local PostgreSQL (`ConnectionRefusedError`), outside the digest path.

## Sprint 6 Production-MVP Readiness
Date: 2026-05-19
Status: implemented

Goal:
- Prepare StudyPilot for a production-ready MVP release with focused infrastructure, deployment, monitoring, smoke, and e2e confidence work.

What was done:
- Added production/runtime settings:
  - `APP_ENV`;
  - `TESTING`;
  - `APP_VERSION`;
  - `LOG_LEVEL`;
  - `LLM_PROVIDER`;
  - `EMBEDDING_PROVIDER`;
  - test-only auth and e2e secret settings.
- Added fail-fast production validation for critical env vars and unsafe production settings:
  - database URL;
  - Telegram bot token;
  - Mini App URL;
  - restricted HTTPS CORS origins;
  - provider keys;
  - vector/embedding config;
  - internal jobs secret;
  - disabled test auth/fake providers/debug mode.
- Added test-only auth support guarded by `APP_ENV=test`, `TESTING=true`, and `TEST_AUTH_ENABLED=true`.
- Added health endpoints:
  - `GET /health` returns status, service, version, and environment;
  - `GET /health/ready` checks database and pgvector readiness and returns `503` when not ready.
- Added hidden test-support endpoints:
  - `POST /api/v1/test/reset`;
  - `POST /api/v1/test/seed`;
  - both require test env and `X-Test-Secret`.
- Added deterministic seed data for e2e:
  - user;
  - plan and stages;
  - focus sessions;
  - documents and chunks;
  - analytics-producing focus data;
  - weekly reviews.
- Added fake deterministic providers for e2e/test mode:
  - roadmap generation;
  - daily plan generation;
  - embeddings;
  - query rewriting;
  - RAG answer generation.
- Added request/error logging middleware with request id, duration, method, path, status code, and env-controlled log level.
- Added Playwright e2e setup under `frontend/e2e`:
  - `npm run test:e2e`;
  - `npm run test:e2e:ui`;
  - Telegram WebApp mock;
  - signed deterministic Telegram `initData`;
  - API reset/seed helpers.
- Added e2e coverage for:
  - app load and visible navigation;
  - auth bootstrap with protected API access;
  - goal to roadmap;
  - Today empty and seeded states;
  - focus start/end/history;
  - Knowledge Base upload/list;
  - RAG answer with sources and no-source disabled state;
  - Analytics empty and seeded states;
  - Weekly Review generate/apply/history through API.
- Added backend tests for:
  - readiness DB failure;
  - test auth enabled/disabled guard;
  - production config validation;
  - sanitized document error output.
- Added frontend resilience polish:
  - global error boundary;
  - route error fallback;
  - Telegram viewport CSS sync;
  - Vitest exclusion for e2e specs.
- Polished Docker setup:
  - backend healthcheck uses `/health`;
  - backend readiness healthcheck uses `/health/ready`;
  - backend and bot run as non-root where feasible;
  - frontend Dockerfile now builds static assets and serves through nginx;
  - frontend nginx `/health` endpoint;
  - `.env` remains excluded from Docker build contexts.
- Updated `docker-compose.prod.yml`:
  - pgvector Postgres;
  - migration ordering;
  - backend readiness healthcheck;
  - frontend healthcheck;
  - bot waits for healthy backend;
  - Caddy waits for healthy backend/frontend.
- Updated GitHub Actions:
  - PR checks include backend ruff/pytest, migration check against pgvector Postgres, frontend typecheck/test/build, and bot import check;
  - added E2E workflow on `workflow_dispatch` and `main` only.
- Updated env/docs:
  - `.env.example`;
  - `.env.production.example`;
  - `.github/SECRETS.md`;
  - `README.md` production, smoke, and e2e sections.
- Added practical docs:
  - `docs/DEPLOYMENT.md`;
  - `docs/MONITORING.md`.

Safety notes:
- No production test-auth bypass is allowed.
- Fake AI/embedding providers are allowed only in test mode.
- E2E setup does not call real OpenAI, Tensorix, or Telegram APIs.
- Health/readiness responses do not expose secrets.
- Request logging avoids request bodies, uploaded document content, and full LLM prompts.
- Frontend secrets remain out of the Vite bundle.
- Weekly Review remains API-only for this sprint; no new Weekly Review UI was added.
- Focus remains the existing Today -> session -> History flow; no standalone Focus tab was added.

Verification:
- `python -m pip install -r backend/requirements.txt` refreshed the local backend venv and installed missing `tzdata`.
- `backend`: `python -m pytest tests -q` passed with `162 passed`, `2 skipped`.
- `backend`: `python -m ruff check app tests` passed.
- `backend`: `python -m ruff format --check app` passed.
- `frontend`: `npm run typecheck` passed.
- `frontend`: `npm run test` passed with `81 passed`.
- `frontend`: `npm run build` passed.
- `frontend`: `npx playwright test --list` found 9 e2e tests.
- `docker compose -f docker-compose.prod.yml config --quiet` passed with dummy production env values.
- `git diff --check` passed.

Known local verification limits:
- Full local Playwright execution was not completed because Chromium was not installed locally and Docker Desktop was not running, so an isolated pgvector e2e database could not be started.
- The GitHub E2E workflow installs Chromium, starts a migrated pgvector-backed test backend with fake providers, and runs `npm run test:e2e`.

## Backlog (Alpha)
Date: 2026-04-18
Status: in progress

- The alpha version of the Roadmap mini app is locked in as the current stage.
- Issue: roadmap generation becomes unstable when the deadline is too close.

## Current Follow-ups

- Replace placeholder API endpoints in analytics and user update/delete with real logic or remove obsolete routes.
- Replace the temporary tunnel URL with a permanent HTTPS domain for stable Mini App testing.
- Keep backend, bot, and frontend `.env` values aligned for production.
- Add a CI pipeline for tests and lint, plus a formal release workflow.

## Notes


-----DEPLOYMENT NOTES-----

- On Windows, `bot` pinned dependencies install reliably with Python 3.12.
- Root and service-level Makefiles currently use Unix-style `.venv/bin/...` commands and need Windows-specific alternatives for direct `make` usage on PowerShell.

 Применил локальный render-deploy skill из скачанного openai/skills.git, потому что этот проект multi-service: FastAPI
  API, Vite frontend, Telegram bot, PostgreSQL/pgvector.

  Сделал:

  - Добавил Render Blueprint: C:/Users/Adam Vakar/OneDrive - TUS MM/Untitled Folder/Code/Agent_RAG/learning-os/
    render.yaml:1
  - Добавил нормализацию Render/Postgres URL для async SQLAlchemy: C:/Users/Adam Vakar/OneDrive - TUS MM/Untitled
    Folder/Code/Agent_RAG/learning-os/backend/app/config.py:123
  - Добавил миграции на старте API с schema_migrations, чтобы рестарты не падали: C:/Users/Adam Vakar/OneDrive - TUS MM/
    Untitled Folder/Code/Agent_RAG/learning-os/backend/scripts/run_migrations.py:15
  - Обновил deployment docs с Render flow и dashboard deeplink: C:/Users/Adam Vakar/OneDrive - TUS MM/Untitled Folder/
    Code/Agent_RAG/learning-os/docs/DEPLOYMENT.md:69
  - Добавил тест на Render-style DB URL.

  Проверки:

  - Backend tests: 163 passed, 2 skipped
  - Ruff на изменённых Python-файлах: passed
  - render.yaml YAML parse: passed
  - tsc --noEmit: passed
  - npm run build локально заблокирован Windows/OneDrive EPERM на запись frontend/tsconfig.tsbuildinfo; vite build тоже
    упёрся в локальный запрет записи временного config-файла. Это похоже на файловую/OneDrive проблему, не на ошибку
    кода.

  Render CLI локально не установлен, поэтому render blueprints validate не запускался. Для деплоя нужно закоммитить и
  запушить изменения, потом открыть:

  https://dashboard.render.com/blueprint/new?repo=https://github.com/Adwerse/Learnify

  В Render надо заполнить sync: false env vars: BOT_TOKEN, MINI_APP_URL, ALLOWED_ORIGINS, OPENAI_API_KEY,
  TENSORIX_API_KEY, VITE_API_BASE_URL.
