# GitHub Actions Secrets

Add secrets in GitHub: `Settings -> Secrets and variables -> Actions`.

## Railway
- `RAILWAY_TOKEN` - `railway.app -> Account Settings -> Tokens`

The workflows use these Railway service names:
- `frontend`
- `backend`
- `bot`

If your services are named differently, update the `service` field in:
- `.github/workflows/deploy-frontend.yml`
- `.github/workflows/deploy-backend.yml`

## Important For Monorepo Setup And `Script start.sh not found`
If Railway analyzes the repository root directly, where `backend/`, `frontend/`, and `bot/` live, Railpack may fail to detect the correct start command.

In this repository the services use Dockerfile-based deploys:
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `bot/Dockerfile`

The matching `railway.toml` files are already configured with:
- `builder = "DOCKERFILE"`
- `dockerfilePath = "Dockerfile"`

The workflows deploy subdirectories through Railway CLI using `--path-as-root`, so each service has its own build context.

Check these Railway settings for each service:
- `backend` -> Root Directory: `backend`
- `frontend` -> Root Directory: `frontend`
- `bot` -> Root Directory: `bot`

If GitHub Autodeploy is enabled for a service, also set the Config File Path using an absolute path:
- `backend`: `/backend/railway.toml`
- `frontend`: `/frontend/railway.toml`
- `bot`: `/bot/railway.toml`

To avoid duplicate and conflicting deploys, keep only one deploy source:
- GitHub Actions, recommended for this repo
- Railway GitHub Autodeploy

## Do You Need A `.env` File For GitHub Actions?
No. Use GitHub Secrets for CI/CD.

## What To Add To Railway Variables At Runtime
These variables are required by the services running on Railway, not by GitHub Actions.

### backend service
- `DATABASE_URL`
- `SECRET_KEY`
- `OPENAI_API_KEY`
- `BOT_TOKEN`
- `MINI_APP_URL`
- `ALLOWED_ORIGINS`, optional but recommended for production
- `DEBUG`, optional

### frontend service
- `VITE_API_BASE_URL`
- `VITE_TELEGRAM_BOT_NAME`

### bot service
- `BOT_TOKEN`
- `MINI_APP_URL`
- `WEBHOOK_URL`, if you use webhook mode
- `WEBHOOK_PATH`, optional, defaults to `/webhook`
- `USE_WEBHOOK`, optional, `true` or `false`
- `DEBUG`, optional

## Verification
1. Create a test PR and confirm that `PR Checks` starts.
2. Merge into `main` and confirm that the deploy workflows start.
3. Verify the frontend URL on Railway.
4. Verify the backend health endpoint at `/health`.
