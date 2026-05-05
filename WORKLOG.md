# Learning OS Work Log

Last updated: 2026-05-05

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
- Updated the bottom tab label from `Knowledge` to `База знаний` and guarded tab text against overflow.
- Added frontend tests for API methods, hooks, formatters, and the main Knowledge Base UI flows.

Checks:
- `npm test` passed with `61 passed`.
- `npm run build` passed.
- Local Vite dev server started and responded with HTTP `200` at `http://localhost:5173/`.

## [Sprint 5] Knowledge Upload Dev Fix
Date: 2026-05-05
Status: completed

What was done:
- Investigated the Mini App failure where document upload showed `Не удалось загрузить файл` and the materials list also failed to load.
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

- On Windows, `bot` pinned dependencies install reliably with Python 3.12.
- Root and service-level Makefiles currently use Unix-style `.venv/bin/...` commands and need Windows-specific alternatives for direct `make` usage on PowerShell.
