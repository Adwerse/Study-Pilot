import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.config import settings
from app.database import engine


logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "studypilot-backend",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@router.get("/health/ready")
async def readiness_check(response: Response) -> dict[str, object]:
    checks: dict[str, str] = {}
    ready = True

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            checks["database"] = "ok"

            if settings.VECTOR_STORE_PROVIDER == "pgvector":
                result = await connection.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                )
                checks["vector_store"] = (
                    "ok" if result.scalar_one_or_none() == 1 else "not_ready"
                )
                ready = ready and checks["vector_store"] == "ok"
            else:
                checks["vector_store"] = "not_configured"
    except Exception:
        logger.exception("Readiness check failed")
        ready = False
        checks.setdefault("database", "not_ready")
        if settings.VECTOR_STORE_PROVIDER == "pgvector":
            checks.setdefault("vector_store", "not_ready")

    response.status_code = (
        status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
    }
