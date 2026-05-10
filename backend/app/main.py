import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, ask, documents, focus, plans, users, weekly_review
from app.config import settings
from app.services.notification_worker import notification_worker_loop


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting Learning OS API")
    notification_task: asyncio.Task | None = None
    if settings.NOTIFICATIONS_ENABLED:
        notification_task = asyncio.create_task(notification_worker_loop())
    try:
        yield
    finally:
        if notification_task is not None:
            notification_task.cancel()
            try:
                await notification_task
            except asyncio.CancelledError:
                logger.info("Notification worker stopped")
        logger.info("Shutting down")


app = FastAPI(title="Learning OS API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(focus.router, prefix="/api/v1")
app.include_router(ask.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(weekly_review.router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
