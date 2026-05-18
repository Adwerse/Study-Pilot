import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, ask, documents, focus, plans, users, weekly_review
from app.config import settings
from app.services.notification_worker import notification_worker_loop
from app.services.weekly_digest_worker import weekly_digest_worker_loop


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting Learning OS API")
    notification_task: asyncio.Task | None = None
    weekly_digest_task: asyncio.Task | None = None
    if settings.NOTIFICATIONS_ENABLED:
        notification_task = asyncio.create_task(notification_worker_loop())
    if settings.WEEKLY_DIGEST_ENABLED:
        weekly_digest_task = asyncio.create_task(weekly_digest_worker_loop())
    try:
        yield
    finally:
        tasks = [
            (notification_task, "Notification worker stopped"),
            (weekly_digest_task, "Weekly digest worker stopped"),
        ]
        for task, stopped_message in tasks:
            if task is None:
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(stopped_message)
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
