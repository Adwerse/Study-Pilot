# GitHub Actions Secrets

Добавь в GitHub: Settings -> Secrets and variables -> Actions.

## Railway
- RAILWAY_TOKEN — railway.app -> Account Settings -> Tokens
- RAILWAY_FRONTEND_SERVICE_ID — ID сервиса frontend в Railway проекте
- RAILWAY_BACKEND_SERVICE_ID — ID сервиса backend в Railway проекте
- RAILWAY_BOT_SERVICE_ID — ID сервиса bot в Railway проекте

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
