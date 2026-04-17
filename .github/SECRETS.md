# GitHub Actions Secrets

Добавь в GitHub: Settings -> Secrets and variables -> Actions.

## Railway
- RAILWAY_TOKEN — railway.app -> Account Settings -> Tokens

В workflows используются имена сервисов Railway:
- frontend
- backend
- bot

Если сервисы у тебя названы иначе, поменяй поле service в:
- .github/workflows/deploy-frontend.yml
- .github/workflows/deploy-backend.yml

## Важно для monorepo и ошибки `Script start.sh not found`
Если Railway анализирует корень репозитория (где лежат `backend/`, `frontend/`, `bot/`), Railpack не может корректно определить старт и падает.

В этом репозитории workflows деплоят подпапки напрямую через Railway CLI с `--path-as-root`, поэтому дополнительный `cp` не нужен.

Проверь в Railway для каждого сервиса:
- `backend` -> Root Directory: `backend`
- `frontend` -> Root Directory: `frontend`
- `bot` -> Root Directory: `bot`

Если у сервиса включён GitHub Autodeploy, выстави ещё Config File Path (абсолютный путь):
- `backend`: `/backend/railway.toml`
- `frontend`: `/frontend/railway.toml`
- `bot`: `/bot/railway.toml`

Чтобы не было двойных и конфликтующих деплоев, оставь только один источник деплоя:
- либо GitHub Actions (рекомендуется в этом репо),
- либо Railway GitHub Autodeploy.

## Нужен ли .env файл для GitHub Actions?
Нет. Для CI/CD используй GitHub Secrets.

## Что добавить в Railway Variables (runtime)
Эти переменные нужны самим сервисам в Railway, не GitHub Actions.

### backend service
- DATABASE_URL
- SECRET_KEY
- OPENAI_API_KEY
- BOT_TOKEN
- MINI_APP_URL
- ALLOWED_ORIGINS (опционально, но рекомендуется для production)
- DEBUG (опционально)

### frontend service
- VITE_API_BASE_URL
- VITE_TELEGRAM_BOT_NAME

### bot service
- BOT_TOKEN
- MINI_APP_URL
- WEBHOOK_URL (если используешь webhook mode)
- WEBHOOK_PATH (опционально, по умолчанию /webhook)
- USE_WEBHOOK (опционально, true/false)
- DEBUG (опционально)

## Проверка
1. Создай тестовый PR: должен стартовать PR Checks.
2. Смёрджи в main: должны стартовать deploy workflows.
3. Проверь frontend URL на Railway.
4. Проверь backend health endpoint: /health.
